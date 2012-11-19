import webapp2
import string
import cgi
import re
import jinja2
import os


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

mainpage="""
<h2>This is the home page</h2>
"""

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
template = jinja_environment.get_template('/templates/signup-form.html')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(mainpage)
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

    def escape_html(self,s):
        return cgi.escape(s, quote = True)

    def post(self):
        text = self.request.get('text')
        newtext = '' 
        for i in text:
            if i in string.letters:
                newtext = newtext + self.encrypt(i)
            if i not in string.letters:
                newtext = newtext + i
        self.response.out.write(form2%{"newtext" : self.escape_html(newtext)})

class WelCome(webapp2.RequestHandler):
    def get(self):
        username = self.request.get('username')
        self.response.out.write("Welcome, " + username)

class SignUp(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(template.render())      

    def escape_html(self,s):
        return cgi.escape(s, quote = True)

    def post(self):
        user_username = self.request.get('username')
        user_password = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')

        username = valid_username(user_username)
        password = valid_password(user_password)
        verify = valid_verify(user_verify, user_password)
        email = valid_email(user_email)
        
        errorflag = False
        params = dict(username = user_username, email = user_email)
        if not username:
            params['error_username'] = "That's not a valid username."
            errorflag = True

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
            self.response.out.write(template.render(**params))
        else:
            self.redirect('/unit2/welcome?username=' + user_username)

app = webapp2.WSGIApplication([('/', MainPage), ('/unit2/rot13', ROT13), ('/unit2/signup', SignUp), ('/unit2/welcome', WelCome)],
                              debug=True)
