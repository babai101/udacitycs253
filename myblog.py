import re
import os
import webapp2
import jinja2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class BlogDb(db.Model):
    #user = db.StringProperty(required = True)
    #password = db.StringProperty(required = True)
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

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
class MainPage(Handler):
    def get(self):
        self.render_front()
class PermaLink(Handler):
    def get(self):
        url = self.request.url
        keyid = int(re.findall(r'/unit3/[0-9]+', url)[0][7:])
        blogs = db.GqlQuery("SELECT * FROM BlogDb ORDER BY created DESC") 
        for blog in blogs:
            if blog.key().id() == keyid:
                self.render("view-post.html", blog = blog)
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
            redirecturl = '/unit3/' + str(keyid)
            self.redirect(redirecturl)   
        else:
            error = "please enter both title and content!" 
            self.render("newpost.html", error = error)

app = webapp2.WSGIApplication([('/unit3', MainPage), ('/unit3/newpost', NewPost), ('/unit3/[0-9]+', PermaLink)], debug=True)
