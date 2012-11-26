import webapp2
import string
import cgi
import re
import jinja2
import os
import hmac
import hashlib
import random
import json
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


SECRET = 'archlinux'

form="""

<h2>Enter some text to ROT13:</h2>
<form method="post" action="/unit2/rot13">
    <textarea name="text" style="height: 100px; width: 400px;">
    </textarea>
    <br>
    <input type="submit">
</form>
"""
form2="""
<h2>Enter some text to ROT13:</h2>
<form method="post" action="/unit2/rot13">
    <textarea name="text" style="height: 100px; width: 400px;">%(newtext)s
    </textarea>
    <br>
    <input type="submit">
</form>
"""

def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

#def makeJson(Handler, kwargs):
#    self.response.out.write(kwargs.title)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    def render_front(self, title="", content=""):
        blogs = db.GqlQuery("SELECT * FROM BlogDb ORDER BY created DESC")
        self.render("front-page.html", title=title, content=content, blogs = blogs)


class BlogDb(db.Model):
    #user = db.StringProperty(required = True)
    #password = db.StringProperty(required = True)
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class UserDb(db.Model):
    user = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)
PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASS_RE.match(password)
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    if not email:
        return True
    else:
        return EMAIL_RE.match(email)
def valid_verify(verify, password):
    if verify == password:
        return True
    else: return False

class MainPage(Handler):
    def get(self):
        self.render_front()

class ROT13(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(form)

    def encrypt(self,c):
        chardigit = ord(c)
        if chardigit >= 97 and chardigit <= 122:
            temp = chardigit + 13
            if temp > 122:
                temp = (temp - 122) + 96 
                return chr(temp)
            return chr(temp)
        if chardigit >= 65 and chardigit <= 90: 
            temp = chardigit + 13 
            if temp > 90:
                temp = (temp - 90) + 64
                return chr(temp)
            return chr(temp)
        else: return None

    
    def post(self):
        text = self.request.get('text')
        newtext = '' 
        for i in text:
            if i in string.letters:
                newtext = newtext + self.encrypt(i)
            if i not in string.letters:
                newtext = newtext + i
        self.response.out.write(form2%{"newtext" : newtext})

class WelCome(webapp2.RequestHandler):
    def get(self):
        user_hashed = self.request.cookies.get('user_id')
        user = check_secure_val(user_hashed)
        if user:
            self.response.out.write("Welcome, " + user)
        else:
            self.redirect('/signup')

class SignUp(Handler):
    def get(self):
        self.render("signup-form.html")      

    def post(self):
        user_username = self.request.get('username')
        user_password = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')

        username = valid_username(user_username)
        password = valid_password(user_password)
        verify = valid_verify(user_verify, user_password)
        email = valid_email(user_email)
        
        users = db.GqlQuery("SELECT * FROM  UserDb")
        errorflag = False
        
        params = dict(username = user_username, email = user_email)

        if not username:
            params['error_username'] = "That's not a valid username."
            errorflag = True
 
        for user in users:
            if user.user == user_username:
                params['error_username'] = "User already exists."
                errorflag =  True

        if not password:
            params['error_password'] = "That wasn't a valid password."
            errorflag = True

        if not verify:
            params['error_verify'] = "Passwords do not match."
            errorflag = True

        if not email:
            params['error_email'] = "That's not a valid email."
            errorflag = True
        if errorflag:
            self.render("signup-form.html", **params)
        else:
            #self.redirect('/unit2/welcome?username=' + user_username)
            password_hashed = make_pw_hash(user_username, user_password)
            a = UserDb(user = user_username, password = password_hashed)
            a.put()
            cookie_hashed = make_secure_val(user_username)
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(cookie_hashed))
            self.redirect('/welcome')

class Login(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        user_username = self.request.get('username')
        user_password = self.request.get('password')
        q = db.GqlQuery("SELECT * FROM UserDb")
        for user in q:
            if user.user == user_username:
                if valid_pw(user_username, user_password, user.password):
                    cookie_hashed = make_secure_val(user_username)
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(cookie_hashed))
                    self.redirect('/welcome')

            else:
                self.render("login.html", error = "invalid login")
                        
class Logout(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % '')
        self.redirect('/signup')

class PermaLink(Handler):
    def get(self):
        url = self.request.url
        keyid = int(re.findall(r'/[0-9]+', url)[0][1:])
        blogs = db.GqlQuery("SELECT * FROM BlogDb ORDER BY created DESC") 
        for blog in blogs:
            if blog.key().id() == keyid:
                self.render("view-post.html", blog = blog)
class PermaLinkJson(Handler):
    def get(self):
        url = self.request.url
        keyid = int(re.findall(r'/[0-9]+', url)[0][1:])
        blogs = db.GqlQuery("SELECT * FROM BlogDb ORDER BY created DESC") 
        for blog in blogs:
            if blog.key().id() == keyid:
                self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
                self.response.out.write(json.dumps({"subject":str(blog.title), "content": str(blog.content)}))

class MainPageJson(Handler):
    def get(self):
        temp = []
        blogs = db.GqlQuery("SELECT * FROM BlogDb ORDER BY created DESC")
        for blog in blogs:
            temp.append({"subject": str(blog.title), "content": str(blog.content)})
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json.dumps(temp))

class NewPost(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        title = self.request.get("subject") 
        content = self.request.get("content")
        if title and content:
            #a = BlogDb()
            a = BlogDb(title = title, content = content)
            a.put()
            keyid = a.key().id()
            redirecturl = '/' + str(keyid)
            self.redirect(redirecturl)   
        else:
            error = "please enter both title and content!" 
            self.render("newpost.html", error = error)
    

app = webapp2.WSGIApplication([('/', MainPage), ('/unit2/rot13', ROT13), ('/signup', SignUp), ('/welcome', WelCome), ('/login', Login), ('/logout', Logout), ('/newpost', NewPost), ('/[0-9]+', PermaLink), ('/[0-9]+\.json', PermaLinkJson), ('/\.json', MainPageJson)], debug=True)
