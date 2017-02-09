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
        u = User.user_by_id(int(user_id))
        u.user_name = user_name
        u.password = user_password
        u.put()
        return u

    @classmethod
    def remove_user(cls, user_id):
        u = User.user_by_id(int(user_id))
        if u.key().id() == user_id:
            u.delete()
            return True

    @classmethod
    def all_users(cls, sortby='name'):
        return User.all().order(sortby)

    @classmethod
    def user_by_name(cls, user_name):
        return User.all().filter('name =', user_name).get()

    @classmethod
    def user_by_id(cls, id):
        return User.all().filter('ids = ', int(id)).get()

    @classmethod
    def user_id_by_username(cls, user_name):
        u = User.all().filter('name = ', user_name).get()
        user_id = int(u.key().id())
        return user_id

    @classmethod
    def user_name_by_userid(cls, user_id):
        return User.all().filter('ids = ', int(user_id)).get()


    @classmethod
    def user_comments(cls, user_id):
        c = Comments.all().filter('user=', int(user_id)).get()
        return c

    @classmethod
    def user_likes(cls, user_id):
        l = Likes.all().filter('user=', int(user_id)).get()
        return l


## Post Model Class
class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    created_by = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    # add a podt
    @classmethod
    def add_post(cls, subject, content, created, created_by, last_modified):
        b = Post(subject=subject, content=content, created=created, created_by=created_by, last_modified=last_modified)
        b.put()
        return b

    @classmethod
    def get_all_posts(cls):
        return Post.all()

    @classmethod
    def get_latest_ten_posts(cls):
        return Post.all().fetch(10)

    @classmethod
    def get_ten_posts_collection(cls):
        posts = Post.all().fetch(10)
        for post in posts:
            # find this post id
            post_id = post.key().id()
            # Find all the comments related to this blog
            comments = db.GqlQuery("select * from Comments where entry=:post_id", post_id=post_id)
            for comment in comments:
                # user_id = comment.user
                subject = comment.content
                date = comment.created.strftime("%b %d, %Y")






## Post Like Model Class
class Likes(db.Model):
    user = db.IntegerProperty(required=False)
    entry = db.IntegerProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

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
        f = Likes(user=user, entry=entry)
        f.put()
        return f

    @classmethod
    def count_likes(cls, entry):
        c = Likes.all()
        count = c.filter('entry=', int(entry)).count()
        return int(count)

    @classmethod
    def remove(cls, user, entry):
        f = cls.get_by_entry(user_id=user, entry_id=entry)

        # make sure that logged in user is unliking their liked entry
        if f and f.user == user:
            f.delete()
            return True


## User Blog Comments DB Model
class Comments(db.Model):
    user = db.IntegerProperty(required=False)
    entry = db.IntegerProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    # add comments
    @classmethod
    def add(cls, user, entry, content):
        c = Comments(user=user, entry=entry, content=content)
        c.put()
        return c

    # update comment
    @classmethod
    def update_comment(cls, post_id, new_comment):
        c = Comments.get_by_postid(int(post_id))
        c.content = new_comment
        c.put()
        return c

    # remove comment
    @classmethod
    def remove_user(cls, user_id):
        u = User.user_by_id(int(user_id))
        if u.key().id() == user_id:
            u.delete()
            return True

    # display all comments
    @classmethod
    def get_all_comments(cls):
        return Comments.all()

    # display latest 10 comments
    @classmethod
    def get_latest_10_comments(cls):
        return Comments.all().fetch(10)

    # display latest ten comments
    @classmethod
    def get_comment_by_id(cls, comment_id):
        return Comments.all().filter('ids =', int(comment_id)).get()

    # display comments by posts
    @classmethod
    def get_all_comments_by_post(cls, post_id):
        return Comments.all().filter("entry=", post_id)

    @classmethod
    def get_comment_user_name(cls, comment_id):
        comment = Comments.all().filter("ids=", int(comment_id)).get()
        user_id = comment.user
        user_name = User.all().filter("ids=", user_id).get()
        return User.user_name_by_userid(user_name)






    @classmethod
    def get_by_postid(cls, post_id):
        return Comments.all().filter('entry =', int(post_id)).get()

    @classmethod
    def get_by_user(cls, user):
        return Comments.all().filter('user =', int(user)).order('-entry')

    @classmethod
    def get_by_entry(cls, entry):
        return Comments.all().filter('entry =', int(entry)).order('created').get()

    @classmethod
    def add(cls, user, entry, content):
        c = Comments(user=user, entry=entry, content=content)
        c.put()
        return c

    @classmethod
    def add_anon(cls, entry, content):
        c = Comments(entry=entry, content=content)
        c.put()
        return c

    @classmethod
    def update(cls, comment_id, user, content):
        c = Comments.get_by_id(comment_id)
        # ensure that user who created comment is same as who is editing
        if user == c.user.key().id():
            c.content = content
            c.put()
            return c

    @classmethod
    def remove(cls, comment_id, user):
        c = Comments.get_by_id(comment_id)
        # make sure that logged in user is same as comment owner
        if c and c.user.key().id() == user:
            c.delete()
            return True
