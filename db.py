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

##### Globals
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)
def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)
PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)



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

## User Blog Comments DB Model
class Comments(db.Model):
    user = db.ReferenceProperty(required=False)
    entry = db.IntegerProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_by_user(cls, user):
        return Comments.all().filter('user =', user).order('-entry')

    @classmethod
    def get_by_entry(cls, entry):
        return Comments.all().filter('entry =', entry).order('created')

    @classmethod
    def add(cls, user, entry, content):
        c = Comments(user=user, entry=entry, content=content)
        c.put()
        return c

    @classmethod
    def update(cls, cid, user, content):
        c = Comments.get_by_id(cid)
        # ensure that user who created comment is same as who is editing
        if user == c.user.key().id():
            c.content = content
            c.put()
            return c

    @classmethod
    def remove(cls, cid, user):
        c = Comments.get_by_id(cid)
        # make sure that logged in user is same as comment owner
        if c and c.user.key().id() == user:
            c.delete()
            return True

