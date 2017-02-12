from db import *


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

##### The main page handler
class MainPage(BlogHandler):
    def get(self):
        # Check if the username cookie exists and save value to variable "username"
        username = self.request.cookies.get('username')
        # get the latest ten posts
        posts = Post.get_latest_ten_posts()
        # If the user already logged in they can not return to the main page
        if username:
            self.render('welcome.html', posts=posts, username=username)
        else:
            self.render('main.html', posts=posts)

##### blog stuff
def blog_key(name='default'):
    return db.Key.from_path('blogs', name)

class BlogFront(BlogHandler):
    def get(self):
        user_name = self.request.cookies.get('username')
        blog_collect_array = []
        posts = db.GqlQuery("select * from Post")
        for post in posts:
            post_id = post.key().id()
            post_comments = Comments.comments_by_post_id(int(post_id))
            post_likes = Likes.all().filter("entry", int(post_id)).count()
            blog_collect_array.insert(post_id, {"blog": post, "comments": post_comments, "likes": int(post_likes)})

        if user_name:
            user_id = User.all().filter("name", user_name).get().key().id()
            self.render('blog_entries.html', posts=posts, blog_collection=blog_collect_array, userid=user_id, username=user_name, name=user_name)
        else:
            self.render('blog_entries.html', posts=posts, blog_collection=blog_collect_array)

    def post(self):
        form_name = self.request.get('form_name')
        post_id = self.request.get('entry_id')
        if form_name == 'comments_form':
            username = self.request.cookies.get('username')
            post_content = self.request.get('comment')
            if username:
                user_id = User.user_id_by_name(username)
                Comments.add(str(username), int(user_id), int(post_id), post_content)
                self.redirect('/blog')
            else:
                Comments.add("guest", int(100), int(post_id), post_content)
                self.redirect('/blog')

        if form_name == 'likes_form':
            username = self.request.cookies.get('username')
            if username:
                user_id = User.user_id_by_name(username)
                Likes.add(int(user_id), int(post_id))
                self.redirect("/blog")
            else:
                Likes.add(int(100), int(post_id))
                self.redirect("/blog")

        if form_name == 'edit_post':
            subject_update = self.request.get('subject')
            content_update = self.request.get('content')
            self.render('edit_post.html', post_id=post_id, subject=subject_update, content=content_update)

        if form_name == 'delete_post':
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            entry = db.get(key)
            entry.delete()
            self.redirect("/blog")

        if form_name == 'update_post':
            subject_update = self.request.get('subject_update')
            content_update = self.request.get('content_update')
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            p = db.get(key)
            p.subject = subject_update
            p.content = content_update
            p.put()
            self.redirect('/blog/' + post_id)



class PostPage(BlogHandler):
    def get(self, post_id):
        blog_collect_array = []
        user_name = self.request.cookies.get('username')
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        comments = Comments.comments_by_post_id(int(post_id))
        blog_likes = Likes.all().filter("entry", int(post_id)).count()
        blog_collect_array.insert(int(post_id), {"blog": post, "comments": comments, "likes": int(blog_likes)})
        if user_name:
            self.render('blog_entry.html', post=post, blog_collection=blog_collect_array, username=user_name, name=user_name)
        else:
            self.render('blog_entry.html', post=post, blog_collection=blog_collect_array)

    def post(self, post_id):
        form_name = self.request.get('form_name')
        if form_name == 'comments_form':
            username = self.request.cookies.get('username')
            post_content = self.request.get('comment')
            post_id = self.request.get('entry_id')
            if username:
                user_id = User.all().filter("name", username).get().key().id()
                Comments.add(str(username), int(user_id), int(post_id), post_content)
                self.redirect('/blog/' + post_id)
            else:
                Comments.add("guest", int(100), int(post_id), post_content)
                self.redirect('/blog/' + post_id)

        if form_name == 'likes_form':
            username = self.request.cookies.get('username')
            user_id = User.all().filter("name", username).get().key().id()
            likes = Likes.all().filter("entry", post_id).count()
            self.write(likes)
            if username:
                Likes.add(user_id, post_id)
                self.redirect("/blog/" + post_id)
            else:
                Likes.add(int(100), int(post_id))
                self.redirect("/blog/" + post_id)

        if form_name == 'edit_post':
            subject_update = self.request.get('subject')
            content_update = self.request.get('content')
            self.render('edit_post.html', post_id=post_id, subject=subject_update, content=content_update)

        if form_name == 'delete_post':
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            entry = db.get(key)
            entry.delete()
            self.redirect("/blog")

        if form_name == 'update_post':
            subject_update = self.request.get('subject_update')
            content_update = self.request.get('content_update')
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            p = db.get(key)
            p.subject = subject_update
            p.content = content_update
            p.put()
            self.redirect('/blog/' + post_id)



class NewPost(BlogHandler):
    def get(self):
        username = self.request.cookies.get('username')
        user_id = User.user_id_by_name(username)
        self.render("newpost.html", username=username, userid=user_id)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        user_name = self.request.get('user_name')
        user_id = self.request.get('user_id')
        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content, created_by=user_name, post_user_id=int(user_id))
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.write("newpost.html", subject=subject, content=content, error=error)


class EditPost(BlogHandler):
    def get(self):
        entry_id = self.request.get('entry_id')
        subject_update = self.request.get('subject')
        content_update = self.request.get('content')
        self.render('edit_post.html', post_id=entry_id, subject=subject_update, content=content_update)


    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        user_cookie = self.request.cookies.get('username')
        post_user = db.GqlQuery("select * from User where name=:user_name", user_name=user_cookie)
        post_user_id = post_user.key().id()
        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content, username=user_cookie, created_by=user_cookie, post_user_id=post_user_id)
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


class Login(BlogHandler):
    def write_error(self):
        self.render('login-form.html', error_login="Username and/or Password do not match!")

    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        secure_password = hashlib.sha256(password).hexdigest()

        if username and password:
            dbpassword = User.user_by_name(username).get().password
            if not dbpassword:
                self.redirect('/signup')
            if dbpassword == secure_password:
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
                               ('/blog/editpost', EditPost),
                               ],
                              debug=True)
