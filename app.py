from flask import Flask,request,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
import os


#Create object of Flask
flask=Flask(__name__)

# SQL ALchemy Config
base = os.path.abspath(os.path.dirname(__file__))
flask.config['SQLALCHEMY_DATABASE_URI']='sqlite:///' + os.path.join(base, 'data.sqlite')

flask.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db = SQLAlchemy(flask)
Migrate(flask,db)
# End of SQLAlchemy Config

# Model Creation
class Url(db.Model):
    __tablename__= 'urls'
    id=db.Column(db.Integer, primary_key=True)
    orig = db.Column(db.Text)
    short= db.Column(db.Text)

    def __init__(self,orig,short):
        self.orig=orig
        self.short=short

    def __repr__(self):
        return "Orig_URL : {} and Short_URL : {}".format(self.orig,self.short)

# Define end points / routes
@flask.route('/',methods=['GET','POST'])
def home():
    if request.method == "POST":

        url = str(request.form.get('url'))
        service = request.form.get('service')

        if not url.startswith('http'):
            url = 'https://'+url

        if service =='isgd':
            short_url=shorten_with_isgd(url)
        else:
            short_url=shorten_with_bitly(url)

        if not short_url:
            return render_template("home.html",error="Error: could not shorten URL.")

        # urls.append((url,short_url))
        new_url_obj=Url(url,short_url) 
        db.session.add(new_url_obj)
        db.session.commit()

        return render_template("home.html",short_url=short_url)
    
    #GET request
    return render_template("home.html")

# Shorten URL here
def shorten_with_isgd(url):
    api_url="https://is.gd/create.php?format=simple&url={}".format(url)
    response = requests.get(api_url)

    if response.status_code==200:
        return response.text.strip()
    else:
        return None
    
def shorten_with_bitly(url):
    BITLY_ACCESS_TOKEN = "3c6eea7ad80f2343e8c13e7cb3b09da900b15f9e"
    api_url="https://api-ssl.bitly.com/v4/shorten"

    headers = {
        "Authorization": "Bearer " + BITLY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "long_url": url
    }
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        return response.json()["link"]
    else:
        return None

@flask.route('/history',methods=['GET'])
def hist():
    urls = Url.query.all()
    return render_template("history.html", urls=urls)


# -- To Clear All the Entries in the DB
@flask.route('/clear')
def clear():
    db.session.query(Url).delete()
    db.session.commit()
    return render_template("history.html")



# Run the app
if __name__=='__main__':
    flask.run(debug=True)