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


## User Model Class
class User(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def add_user(cls, name, pw, email=None):
        u = User(name=name, password=pw, email=email)
        u.put()
        return u

    @classmethod
    def update_user(cls, user_id, user_name, user_password):
        u = User.user_by_id(int(user_id)).get()
        u.user_name = user_name
        u.password = user_password
        u.put()
        return u

    @classmethod
    def remove_user(cls, user_id):
        u = User.user_by_id(int(user_id)).get()
        if u.key().id() == user_id:
            u.delete()
            return True

    @classmethod
    def all_users(cls, sortby='name'):
        return User.all().order(sortby)

    @classmethod
    def user_by_name(cls, user_name):
        return db.GqlQuery("select * from User where name=:name", name=user_name)
        # return User.all().filter('name=', user_name)

    @classmethod
    def user_by_id(cls, user_id):
        return db.GqlQuery("select * from User where ids=:userid", userid=int(user_id))

    @classmethod
    def user_id_by_name(cls, user_name):
        u = User.all().filter("name", user_name).get().key().id()
        # u = User.user_by_name(user_name).get().id
        return u

    @classmethod
    def user_name_by_id(cls, user_id):
        # u = User.user_by_id(user_id).get().name
        u = User.all().filter('ids', user_id).get().name
        # user_name = u.key().name()
        return u

    @classmethod
    def user_comments(cls, user_id):
        c = Comments.all().filter('user', int(user_id)).fetch(100)
        return c

    @classmethod
    def comments_by_user_id(cls, user_id):
        c = Comments.all().filter('user', int(user_id)).fetch(100)
        return c

    @classmethod
    def comments_by_user_name(cls, user_name):
        c = Comments.all().filter('user', user_name).fetch(100)
        return c

    @classmethod
    def user_likes(cls, user_id):
        l = Likes.all().filter('user', int(user_id)).get()
        return l

    @classmethod
    def likes_by_user_id(cls, user_id):
        l = Likes.all().filter('user', int(user_id)).get()
        return l

    @classmethod
    def likes_by_user_name(cls, user_id):
        l = Likes.all().filter('user', int(user_id)).get()
        return l


## Post Model Class
class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    created_by = db.StringProperty(required=True)
    post_user_id = db.IntegerProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    # add a podt
    @classmethod
    def add_post(cls, subject, content, created_by, post_user_id, last_modified):
        b = Post(subject=subject, content=content, created_by=created_by, last_modified=last_modified, post_user_id=int(post_user_id))
        b.put()
        return True

    @classmethod
    def post_by_id(cls, post_id):
        return Post.all().filter('ids', int(post_id)).get()

    @classmethod
    def get_all_posts(cls):
        return Post.all()

    @classmethod
    def get_latest_ten_posts(cls):
        return Post.all().fetch(10)

    @classmethod
    def get_post_collection(cls, post_id):
        # p = db.GqlQuery("select * from Post where ids=:post_id", post_id=int(post_id))
        p = Post.post_by_id(int(post_id))
        comments = Comments.comments_by_post_id(int(post_id))
        likes = Likes.count_entry_likes(int(post_id))
        # comments = Comments.all().filter('entry=', int(post_id)).fetch(1000)
        # likes = Likes.all().filter('entry=', int(post_id)).count()
        post_collection = [post_id, {"post": p, "comments": comments, "likes": likes}]
        return post_collection

    @classmethod
    def delete_post(cls, entry_id):
        p = Post.all().filter("ids", entry_id).get()
        p.delete()
        return True


## Post Like Model Class
class Likes(db.Model):
    user = db.IntegerProperty(required=False)
    entry = db.IntegerProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def count_entry_likes(cls, post_id):
        return Likes.all().filter('entry=', int(post_id)).count()

    @classmethod
    def get_by_user(cls, user_id):
        return Likes.all().filter('user =', int(user_id)).order('-entry')

    @classmethod
    def get_by_entry(cls, user_id, post_id):
        return Likes.all().filter('user =', int(user_id)).filter('entry =', int(post_id)).order('-entry').get()

    @classmethod
    def get_by_anon_entry(cls, post_id):
        return Likes.all().filter('entry =', int(post_id)).order('-entry').get()

    @classmethod
    def add(cls, user, entry):
        f = Likes(user=user, entry=int(entry))
        f.put()
        return f

    @classmethod
    def count_likes(cls, entry):
        c = Likes.all()
        count = c.filter('entry=', int(entry)).count()
        return int(count)

    @classmethod
    def remove(cls, user, entry):
        f = cls.get_by_entry(user_id=user, entry_id=int(entry))

        # make sure that logged in user is unliking their liked entry
        if f and f.user == user:
            f.delete()
            return True


## User Blog Comments DB Model
class Comments(db.Model):

    user_id = db.IntegerProperty(required=False)
    user = db.StringProperty(required=False)
    entry = db.IntegerProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    # add comments
    @classmethod
    def add(cls, user, user_id, entry, content):
        c = Comments(user=user, user_id=user_id, entry=entry, content=content)
        c.put()
        return c

    # update comment
    @classmethod
    def update_comment(cls, post_id, new_comment):
        c = Comments.comments_by_post_id(int(post_id))
        c.content = new_comment
        c.put()
        return c

    @classmethod
    def comments_by_id(cls, comment_id):
        return Comments.all().filter('entry', int(comment_id)).get()

    @classmethod
    def comments_by_post_id(cls, post_id):
        return Comments.all().filter('entry', int(post_id)).fetch(1000)
