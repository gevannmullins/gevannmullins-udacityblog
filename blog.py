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
        # If the user already logged in they can not return to the main page
        if username:
            self.redirect('/welcome')
        else:
            self.render('main.html')


##### blog stuff

def blog_key(name='default'):
    return db.Key.from_path('blogs', name)


class LikesHandler(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        username = self.request.cookies.get('username')
        if username:
            user = User.user_by_name(username)
            user_id = user.key().id()
            entry = self.request.get('entry')
            Likes.add(user_id, int(entry))
            entry_likes = Likes.count_entry_likes(entry)
            self.render('front.html', posts=posts, entry_likes=entry_likes)
        else:
            self.render('front.html', posts=posts)
            # self.redirect('/blog', posts=posts, entry_likes=entry_likes)


class BlogFront(BlogHandler):
    def get(self):
        user_cookie = self.request.cookies.get('username')
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        if user_cookie:
            self.render('front.html', posts=posts, username=user_cookie, name=user_cookie)
        else:
            self.render('front.html', posts=posts)

    def post(self):
        # key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        # post = db.get(key)

        form_name = self.request.get('form_name')
        content = self.request.get('content')
        username = self.request.cookies.get('username')
        user = User.user_by_name(username)
        user_id = user.key().id()
        self.write(form_name)
        self.write(username)
        self.write(content)
        self.write(user_id)
        # if self.request.get('form_name') == 'comments_form':

            # user = self.request.cookies.get('username')
            # entry = self.request.get('entry')
            # content = self.request.get('content')
            # if entry and content:
            #     Comments.add('gevann', entry, content)
            #     # self.redirect('/blog')
            #
            #     self.render('front.html')

class PostPage(BlogHandler):
    def get(self, post_id):
        user_cookie = self.request.cookies.get('username')
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post=post, username=user_cookie, name=user_cookie)

    def post(self):
        if self.request.get('form_name') == 'comments_form':
            user = self.request.cookies.get('username')
            entry = self.request.get('entry')
            content = self.request.get('content')
            if entry and content:
                Comments.add('gevann', entry, content)
                self.redirect('/blog')



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
                               ('/blog/likes/?', LikesHandler),
                               ],
                              debug=True)
