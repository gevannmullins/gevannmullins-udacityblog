#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import re
import webapp2
import jinja2
import hashlib
import hmac
import random
import string
from string import letters

# google apps engine library import
from google.appengine.ext import db



# jinja2 configuration
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


# SECRET KEY FOR HASH
security_key = 'Python Multi User Blog'


#
# cookie hash functions
#
def make_secure_val(val):
    return '{0}|{1}'.format(val, hmac.new(security_key, val).hexdigest())

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


# Blog Handler Class
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # cookie definitions
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


# post render definitions
def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)


# Main Page Handler Class
class MainPage(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')
        if username:
            self.redirect('/welcome')
        else:
            self.render('main_page.html')


##### blog stuff
def blog_key(name='default'):
    return db.Key.from_path('blogs', name)



### Database Models
# Post Model
class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    created_by = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p=self)

# User Model
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


# Blog Index List
class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts=posts)

# Single Blog Post Handler
class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post=post)

# New Blog Post Handler
class NewPost(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')
        self.render("newpost.html", created_by=username)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        created_by = self.request.cookies.get('username')

        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content, created_by=created_by)
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


### Login, Logout, Signup Classes
# login handler class
class Login(BlogHandler):
    def get(self):
        all_users = User.all_users()
        self.render('login-form.html', users=all_users)

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            u = User.user_by_name(username)

            if u and password == u.password:
                # self.render('login-form.html', error_login=username + ' - ' + password + ' - valid username and password')
                # self.set_secure_cookie('user_id', str(u.key().id()))
                self.set_secure_cookie('username', str(u.name))
                self.redirect('/welcome')
            else:
                self.render('login-form.html', error_login=username + ' - ' + password + ' - username and passwords do not match')
        else:
            self.render('login-form.html', error_login='Please enter your Username and Password to continue')

# logout handler class
class Logout(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')
        self.response.delete_cookie('username')
        # self.request.cookies.clear()
        self.redirect('/')

# signup handler class
class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username=username,email=email)

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
            self.redirect('/welcome?username=' + username)


class Welcome(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')

        if username:
            self.render('welcome.html', username=username)
        else:
            self.redirect('/login')


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/login', Login),
                               ('/welcome', Welcome),
                               ('/newpost', NewPost),
                               ('/logout', Logout),
                               ('/rot13', Rot13),
                               ('/signup', Signup),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ],
                              debug=True)
