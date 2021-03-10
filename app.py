import shutil
import sys
import os
import pymongo
import json
import urllib
import gridfs
import time
from flask import Flask,render_template, url_for, flash, redirect, request, session
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap

from wtforms import StringField, IntegerField, SubmitField, SelectField, PasswordField, validators, SelectMultipleField
import email_validator
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from wtforms.validators import InputRequired, Email, DataRequired
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea
from bson import ObjectId

from flask_wtf.file import FileField, FileRequired, FileAllowed

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'blah blah blah blah'
client = pymongo.MongoClient("mongodb+srv://ubs:" + urllib.parse.quote('ubs@12345') + "@cluster0.qxrt7.mongodb.net/ubs?retryWrites=true&w=majority")
db = client.University_Bazar_db
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'uploads')


photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

class registerForm(FlaskForm):
	firstName = StringField('First Name', [validators.DataRequired()])
	lastName = StringField('Last Name', [validators.DataRequired()])
	emailID = EmailField('Email ID', [validators.DataRequired(),validators.Email()])
	password = PasswordField('Password', [validators.DataRequired()])
	submit = SubmitField('submit')

class LoginForm(FlaskForm):
	emailID = StringField('email ID')
	password = PasswordField('Password')
	submit = SubmitField('Submit')

class createPostForm(FlaskForm):
	Title = StringField('Title',[validators.DataRequired()])
	Type = SelectField(
		'Type',
		choices=[('Exchange', 'Exchange'), ('Sales', 'Sales'), ('Ad', 'Ad')]
	)
	Description = StringField('Description',[validators.DataRequired()], widget=TextArea())
	Image = FileField(validators=[FileAllowed(photos, 'Image only!'), FileRequired('File was empty!')])
	Clubs = SelectMultipleField('Share To Clubs')
	Users = StringField('Comma separated Emails',widget=TextArea())
	submit = SubmitField('Create')





class searchbar(FlaskForm):
	search = StringField('Search' ,[validators.DataRequired()], render_kw={"placeholder": "Search"})

class createpost(FlaskForm):
	title = StringField('Title',[validators.DataRequired()])
	posttype = SelectField(
		'posttype',
		choices=[('Exchange', 'Exchange'), ('Sales', 'Sales'), ('Ad', 'Ad')]
	)
	description = StringField('description',[validators.DataRequired()], widget=TextArea())
	shareTo = SelectField('Share To',[validators.DataRequired()])
	submit = SubmitField('Create')

@app.route('/register',methods=['GET','POST'])
def register():
	form = registerForm()
	if request.method == 'POST':
		if form.validate_on_submit():
			userData = db.userData_db.find_one({'EmailID': form.emailID.data})
			if userData is None:
				userDataRegistraion = {'FirstName': form.firstName.data, 'LastName': form.lastName.data, 'EmailID': form.emailID.data ,'Password': form.password.data }
				db.userData_db.insert_one(userDataRegistraion).inserted_id
				msg = "Registration Succesful Please Login"
				return render_template('register.html',form=form, msg=msg)
			else:
				msg ="User already exists please login"
				return render_template('register.html',form=form, msg=msg)
	return render_template('register.html',form=form)

@app.route('/createPost',methods=['GET','POST'])
def createPost():
	if(('EmailID' not in session)):
		print('Redirect')
		return redirect('/login')
	msg = ""

	form = createPostForm()
	SearchForm = searchbar()
	userData = db.userData_db.find_one({'EmailID': session['EmailID']})
	postTo = []
	if 'Clubs' in userData:
		for club in userData['Clubs']:
			newTuple = (club,club)
			postTo.append(newTuple)
	form.Clubs.choices = postTo
	print(form.Clubs.choices)
	if request.method == 'POST':
		if form.validate_on_submit():
			searchString = SearchForm.search.data
			fs = gridfs.GridFS(db)
			file_id = fs.put(form.Image.data, filename=form.Image.data.filename)
			sendToUsers =form.Users.data
			paymentRequired = False
			if form.Type.data == 'Sales':
				paymentRequired = True
			sendToUsersList =  sendToUsers.split(',')
			PostData = {'Title': form.Title.data,
						'Type': form.Type.data,
						'Description': form.Description.data,
						'Image': file_id,
						'TimeStamp':time.time() ,
						'postedBy':session['EmailID'],
						'postToClubs': form.Clubs.data,
						'PaymentRequired':paymentRequired,
						'postToUsers':sendToUsersList}
			db.posts.insert_one(PostData).inserted_id
			msg = "Create Post Succesful"

			# image_data = fs.get(ObjectId('60446568ab7abf152435dd5d'))
			# image_data = image_data.read()
			return render_template('createpost.html', msg=msg,form = form, SearchForm=SearchForm,searchString=searchString)
		else:
			msg = "invalid inputs"

	return render_template('createpost.html', form=form,msg=msg,SearchForm=SearchForm)


@app.route('/',methods=['GET','POST'])
def base():
	return redirect('/login')

# ROUTES!
@app.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	msg = ""
	if form.validate_on_submit():
		emailID = form.emailID.data
		password = form.password.data
		userData = db.userData_db.find_one({'EmailID': emailID})
		if(userData is None):
			msg="User not found"
		else:
			try:
				storedPassword = userData["Password"]
				if(storedPassword!=password):
					msg = "password do not match"
				else:
					session['EmailID'] = userData['EmailID']
					session['FirstName'] = userData['FirstName']
					session['LastName'] = userData['LastName']
					return redirect('/homepage')
			except:
				msg = "some error occured"
		return render_template('login.html',form=form,msg=msg)
	return render_template('login.html',form=form,msg=msg)

@app.route('/logout',methods=['GET'])
def logout():
	session.pop("EmailID", None)
	session.pop("FirstName", None)
	session.pop("LastName", None)
	print(session)
	return redirect('/login')

@app.route('/homepage',methods=['GET','POST'])
def homepage():
	searchbarform = searchbar()
	createpostform = createpost()
	# Checking session
	print(session)

	if(('EmailID' not in session)):
		print('Redirect')
		return redirect('/login')

	cards = [
      {
        "postType": "exc",
        "title" : "Philosophy Quotes",
        "body" : "'Whereof one cannot speak, thereof one must be silent' – Ludwig Wittgenstein",
        "image" : "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__340.jpg"
      },
      {
        "postType": "ad",
        "title" : "Pepsi",
        "body" : "Watch, interact and learn more about the songs, characters, and celebrities that appear in your favorite Pepsi TV Commercials.",
        "image" : "https://i1.wp.com/www.blogtowers.com/wp-content/uploads/2019/07/pepsi.png?fit=789%2C432"
      },
      {
        "postType": "sal",
        "title" : "Trek Bicycle East Tarrant County",
        "body" : "Cycling shop offering sales & service of a wide range of bikes, plus clothing, parts & accessories.",
        "image" : "https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/bike-for-sale-06-1570044268.jpg?resize=480:*"
      },
    ]
	
	if searchbarform.validate_on_submit():
		searchString = searchbarform.search.data
		print(searchString)
		return render_template('homepage.html',createpostform=createpostform, searchbarform=searchbarform, searchString=searchString, cards=cards)

	if createpostform.validate_on_submit():
		title = createpostform.title.data
		posttype = createpostform.posttype.data
		description = createpostform.description.data
		shareTo = createpostform.shareTo.data
		print(title, posttype)
		return render_template('homepage.html',createpostform=createpostform, searchbarform=searchbarform, cards=cards)
		
	return render_template('homepage.html',createpostform=createpostform, searchbarform=searchbarform, cards=cards)


@app.route('/messages',methods=['GET'])
def messages():
	form = searchbar()

	# Checking session
	print(session)

	if(('EmailID' not in session)):
		print('Redirect')
		return redirect('/login')

	if form.validate_on_submit():
		searchString = form.search.data
		print(searchString)
		return render_template('messages.html',form=form, searchString=searchString)
	return render_template('messages.html',form=form)


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
	return render_template('404.html',title='404')


port = int(os.getenv('PORT', '3000'))

if __name__ == "__main__":
	app.run(host='127.0.0.1', port=port)