import os
import jinja2
import webapp2
import cgi
import re
import datetime
import random
import hashlib
import hmac
import string
from string import letters

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

SECRET_KEY = 'udacityblog'

#
# cookie hash functions
#
def make_secure_val(val):
    return '{0}|{1}'.format(val, hmac.new(SECRET_KEY, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

#
# user password hash functions
#
def make_salt():
    return ''.join(random.choice(string.letters) for i in range(5))

def make_pw_hash(name, pw, salt=None):
    salt = salt or make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()

    return '{0},{1}'.format(salt, h)

def is_valid_pw(name, pw, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, pw, salt)



def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    # def write(self, template, **params):
    #     t = jinja_env.get_template(template)
    #
    #     always send self.user to template
    # params.update({'user': self.user})
    #
    # self.response.write(t.render(params))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    #store cookies
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def clear_secure_cookie(self, name):
        cookie_val = self.response.headers.clear()

    # def login(self, user):
    #     self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.get_by_id(int(uid))

    def render_post(response, post):
        response.out.write('<b>' + post.subject + '</b><br>')
        response.out.write(post.content)

class MainPage(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = self.request.cookies.get('visits', '0')
        #make sure visits is an integer
        if visits.isdigit():
            visits = int(visits) + 1
            h = hashlib.sha256('welcome gevann').hexdigest()

        else:
            visits = 0
        # visits += 1
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % visits)
        self.response.headers.add_header('Set-Cookie', 'hashes=%s' % h)
        self.write("You've been here %s times!" % visits)
        self.write("You're hash is %s " % h)
        # self.render('main_page.html')

##### blog stuff

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        username = User.get_current_user()
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts, username = username)
        self.write(posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        username = User.get_current_user()
        self.render("newpost.html", username = username)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

###### Unit 2 HW's
class Rot13(BlogHandler):
    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render('rot13-form.html', text = rot13)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

#
# Database Entities
#
class User(db.Model):
    name = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def get_current_user(cls):
        return User.name

    @classmethod
    def get_all(cls, sortby='name'):
        return User.all().order(sortby)

    @classmethod
    def get_by_name(cls, name):
        return User.all().filter('name =', name).get()

    @classmethod
    def get_by_id(cls, ids, parent=None, **kwargs):
        return User.all().filter('ids = ', ids).get()

    @classmethod
    def add(cls, name, pw, email=None):
        u = User(name = name, password = pw, email = email)
        u.put()
        return u

class LoginHandler(BlogHandler):
    def write_error(self):
        # self.write('login-form.html', error_login="Invalid Login")
        self.render('login-form.html', error_login="Invalid Login")

    def get(self):
        # self.write('login-form.html')
        self.render('login-form.html')

    def post(self):
        # validate credentials
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            rs = User.get_by_name(username)

            if rs and valid_password(password):
                # self.login(username)
                self.response.headers.add_header('Set-Cookie', 'username=%s' % username)
                self.set_secure_cookie('user_id', str(rs.key().id()))
                self.redirect('/welcome?username=' + username)
            else:
                self.write_error()
        else:
            self.write_error()

class Signup(BlogHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username, email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            User.add(username, password, email)
            self.redirect('/welcome?username=' + username)

class LogoutHandler(BlogHandler):
    def get(self):
        # self.read_secure_cookie(self, User.get_current_user())
        self.clear_secure_cookie(self, User.get_current_user())
        self.logout()
        self.redirect('/')

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/rot13', Rot13),
                               ('/signup', Signup),
                               ('/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/newpost', NewPost),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler),
                               ],
                              debug=True)
