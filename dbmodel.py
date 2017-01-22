# The database-model
#
#
#
#
#
#
#
#
#
#
#
import re
from google.appengine.ext import db

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

        # @classmethod
        # def user_is_valid(cls, username, password):



