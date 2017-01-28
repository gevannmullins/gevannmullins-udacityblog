import os
import re
import webapp2
import jinja2
import json
import cgi
import datetime
import random
import hashlib
import hmac
import string
from string import letters

# load the google app db
from google.appengine.ext import db

# set the root for templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

SECRET = 'gevann udacity blog'


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)


##### The main page handler
class MainPage(BlogHandler):
    def get(self):
        # Check if the username cookie exists and save value to variable "username"
        username = self.request.cookies.get('username')
        # If the user already logged in they can not return to the main page
        if username:
            self.redirect('/welcome')
        else:
            self.render('main.html')


##### blog stuff

def blog_key(name='default'):
    return db.Key.from_path('blogs', name)




##### the database model handlers

## Post Model Class
class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    created_by = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p=self)


## User Model Class
class User(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def all_users(cls, sortby='name'):
        return User.all().order(sortby)

    @classmethod
    def user_by_name(cls, name):
        return User.all().filter('name =', name).get()

    @classmethod
    def user_by_id(cls, ids):
        return User.all().filter('ids = ', ids).get()

    @classmethod
    def add_user(cls, name, pw, email=None):
        u = User(name=name, password=pw, email=email)
        u.put()
        return u


## Post Like Model Class
class Likes(db.Model):
    user = db.IntegerProperty(required=False)
    entry = db.IntegerProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_by_user(cls, uid):
        return Likes.all().filter('user =', uid).order('-entry')

    @classmethod
    def get_by_entry(cls, uid, eid):
        return Likes.all().filter('user =', uid).filter('entry =', eid).order('-entry').get()

    @classmethod
    def add(cls, user, entry):
        f = Likes(user=user, entry=entry)
        f.put()
        return f

    @classmethod
    def count_entry_likes(cls, entry):
        entry_count = db.GqlQuery("SELECT * FROM Likes")
        return entry_count.count()



    @classmethod
    def remove(cls, user, entry):
        f = cls.get_by_entry(uid=user, eid=entry)

        # make sure that logged in user is unliking their liked entry
        if f and f.user == user:
            f.delete()
            return True

class LikesHandler(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        username = self.request.cookies.get('username')
        user = User.user_by_name(username)
        user_id = user.key().id()
        entry = self.request.get('entry')
        Likes.add(user_id, int(entry))
        entry_likes = Likes.count_entry_likes(entry)
        self.render('front.html',  posts=posts, entry_likes=entry_likes)
        # self.redirect('/blog', posts=posts, entry_likes=entry_likes)


class BlogFront(BlogHandler):
    def get(self):
        user_cookie = self.request.cookies.get('username')
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        if user_cookie:
            self.render('front.html', posts=posts, username=user_cookie, name=user_cookie)
        else:
            self.render('front.html', posts=posts)


class PostPage(BlogHandler):
    def get(self, post_id):
        user_cookie = self.request.cookies.get('username')
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post=post, username=user_cookie, name=user_cookie)


class NewPost(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')
        self.render("newpost.html", username=username)

    def post(self):

        subject = self.request.get('subject')
        content = self.request.get('content')
        user_cookie = self.request.cookies.get('username')
        name_cookie = self.request.cookies.get('name')

        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content, username=user_cookie, created_by=user_cookie)
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

        self.render('rot13-form.html', text=rot13)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return username and USER_RE.match(username)


PASS_RE = re.compile(r"^.{3,20}$")


def valid_password(password):
    return password and PASS_RE.match(password)


EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_email(email):
    return not email or EMAIL_RE.match(email)


class Login(BlogHandler):
    def write_error(self):
        self.write('login-form.html', error_login="Username and/or Password do not match!")

    def get(self):
        self.render('login-form.html')

    def post(self):
        # validate credentials
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            u = User.user_by_name(username)

            if u.password == hashlib.sha256(password).hexdigest():
                self.response.set_cookie('username', str(username))
                self.response.set_cookie('name', str(username))
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
        secure_password = hashlib.sha256(password).hexdigest()

        # check if username already exists

        params = dict(username=username, email=email)

        db_user = User.user_by_name(username)
        if db_user:
            params['error_username'] = "Username already exists."
            have_error = True

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
            User.add_user(username, secure_password, email)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers.add_header('Set-Cookie', 'username=%s' % str(username))
            self.response.headers.add_header('Set-Cookie', 'name=%s' % str(username))
            self.redirect('/welcome?username=' + username)


# logout handler class
class Logout(BlogHandler):
    def get(self):
        self.response.delete_cookie('username')
        self.response.delete_cookie('name')
        self.redirect('/')


class Welcome(BlogHandler):
    def get(self):
        user_cookie = self.request.cookies.get('username')
        name_cookie = self.request.cookies.get('name')
        if user_cookie:
            self.render('welcome.html', username=user_cookie, name=name_cookie)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/rot13', Rot13),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/signup', Signup),
                               ('/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/likes', LikesHandler),
                               ],
                              debug=True)
