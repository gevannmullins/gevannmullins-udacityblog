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

        # Create all the variables/objects/arrays
        blog_collect_dict = dict()
        blog_collect_array = []
        comment_users_array = []

        # List all the blogs
        posts = db.GqlQuery("select * from Post")
        # Loop through each Blog
        for post in posts:
            # find this post id
            post_id = post.key().id()
            # Find all the comments related to this blog
            post_comments = Comments.get_all_comments_by_post(post_id)
            # for post_comment in post_comments:


            # self.write("<br />")
            # self.write("<br />")
            # self.write(list(post_comments))
            # self.write("<br />")
            # self.write("<br />")
            # self.write("<br />")
            # self.write("<br />")
            # self.write("<br />")
            # self.write("<br />")

            # find all the likes related to this blog
            blog_likes = db.GqlQuery("select * from Likes where entry=:post_id", post_id=post_id).count()
            # build the data collection
            blog_collect_dict.update({"blog": post, "comments": post_comments, "likes": int(blog_likes)})
            # save new data collection to an array
            blog_collect_array.insert(post_id, {"blog": post, "comments": post_comments, "likes": blog_likes})

        # if user_name exists then pass it along else only render the post
        if user_name:
            self.render('blog_entries.html', posts=posts, blog_collection=blog_collect_array, username=user_name, name=user_name)
        else:
            self.render('blog_entries.html', posts=posts, blog_collection=blog_collect_array)

    def post(self, post_id):
        # first find the name of the form
        form_name = self.request.get('form_name')

        if form_name == 'comments_form':
            blog_comments = Comments.all().filter('entry =', int(post_id)).get()
            # comments_blog = Post.all().filter('entry =', int(post_id)).get()
            # blog_comments = db.GqlQuery("select * from Comments where entry=:post_id order by created desc limit 10", post_id=post_id)

            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            username = self.request.cookies.get('username')
            user = User.user_by_name(username)
            user_id = user.key().id()
            likes = int(Likes.count_likes(post_id))

            post_content = self.request.get('comment')
            # post_comments = Comments.get_by_postid(int(post_id))

            if username:
                Comments.add(int(user_id), int(post_id), post_content)
                self.redirect('/blog')
                # self.render("permalink.html", post=post, username=username, name=username, comments=post_comments, likes=likes)
            else:
                Comments.add(int(100), int(post_id), post_content)
                self.redirect('/blog')
                # self.render('permalink.html', post=post, comments=post_comments, likes=likes)

        if form_name == 'likes_form':
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            username = self.request.cookies.get('username')
            user = User.user_by_name(username)
            user_id = user.key().id()
            likes = int(Likes.count_likes(post_id))

            post_comments = Comments.get_all_comments()
            if username:
                Likes.add(int(user_id), int(post_id))
                self.redirect("/blog")
                # self.render("blog_entries.html", post=post, username=username, name=username, comments=post_comments, likes=likes)
            else:
                Likes.add(int(100), int(post_id))
                self.redirect("/blog")
                # self.render('blog_entries.html', post=post, comments=post_comments, likes=likes)


class PostPage(BlogHandler):
    def get(self, post_id):
        # Create all the variables/objects/arrays
        blog_collect_dict = dict()
        blog_collect_array = []
        # get the user_name
        user_name = self.request.cookies.get('username')
        # get the blog entry
        # post = Post.get_blog_by_id(post_id)
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        # Find all the comments related to this blog
        comments = db.GqlQuery("select * from Comments where entry=:post_id", post_id=int(post_id)).fetch(1000)
        # find all the likes related to this blog
        blog_likes = db.GqlQuery("select * from Likes where entry=:post_id", post_id=int(post_id)).count()
        # build the data collection
        # blog_collect_dict.update({"blog": post, "comments": comments, "likes": int(blog_likes)})
        # save new data collection to an array
        blog_collect_array.insert(int(post_id), {"blog": post, "comments": comments, "likes": blog_likes})
        # if user_name exist then pass it along else

        # self.write(list(comments))

        if user_name:
            self.render('blog_entry.html', post=post, blog_collection=blog_collect_array, comments=comments, blog_likes=blog_likes, username=user_name, name=user_name)
        else:
            self.render('blog_entry.html', post=post, blog_collection=blog_collect_array, comments=comments, blog_likes=blog_likes)

    def post(self, post_id):
        # first find the name of the form
        form_name = self.request.get('form_name')

        if form_name == 'comments_form':
            blog_comments = Comments.all().filter('entry =', int(post_id)).get()
            # comments_blog = Post.all().filter('entry =', int(post_id)).get()
            # blog_comments = db.GqlQuery("select * from Comments where entry=:post_id order by created desc limit 10", post_id=post_id)

            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            username = self.request.cookies.get('username')
            user = User.user_by_name(username)
            user_id = user.key().id()
            likes = int(Likes.count_likes(post_id))

            post_content = self.request.get('comment')
            # post_comments = Comments.get_by_postid(int(post_id))

            if username:
                Comments.add(int(user_id), int(post_id), post_content)
                self.redirect("/blog/" + int(post_id))
                # self.render("blog_entry.html", post=post, username=username, name=username)
            else:
                Comments.add(int(100), int(post_id), post_content)
                self.redirect("/blog/" + int(post_id))
                # self.render('blog_entry.html', post=post)

        if form_name == 'likes_form':
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            username = self.request.cookies.get('username')
            user = User.user_by_name(username)
            user_id = user.key().id()
            likes = int(Likes.count_likes(post_id))

            post_comments = Comments.get_all_comments()
            if username:
                Likes.add(int(user_id), int(post_id))
                self.render("/blog/" + post_id)
                # self.render("permalink.html", post=post, username=username, name=username, comments=post_comments, likes=likes)
            else:
                Likes.add(int(100), int(post_id))
                self.render("/blog/" + post_id)
                # self.render('permalink.html', post=post, comments=post_comments, likes=likes)


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
            # p = Post(parent=blog_key(), subject=subject, content=content, username=user_cookie, created_by=user_cookie)
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
                               # ('/blog/([0-9]+)', SinglePostPage),
                               ('/blog/newpost', NewPost),
                               # ('/blog/likes/?', LikesHandler),
                               ],
                              debug=True)
