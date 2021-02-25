import shutil
import sys
import os
import pymongo
import json
import urllib
from flask import Flask,render_template, url_for, flash, redirect, request, session
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, SubmitField, SelectField, PasswordField, validators
import email_validator
from wtforms.validators import InputRequired, Email, DataRequired
from wtforms.fields.html5 import EmailField

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'blah blah blah blah'
client = pymongo.MongoClient("mongodb+srv://ubs:" + urllib.parse.quote('ubs@12345') + "@cluster0.qxrt7.mongodb.net/ubs?retryWrites=true&w=majority")
db = client.University_Bazar_db


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

class searchbar(FlaskForm):
	search = StringField('Search' ,[validators.DataRequired()], render_kw={"placeholder": "Search"})

@app.route('/register',methods=['GET','POST'])
def register():
	form = registerForm()
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
	form = searchbar()
	# Checking session
	print(session)

	if(('EmailID' not in session)):
		print('Redirect')
		return redirect('/login')

	cards = [
			{
				"postType": "exc",
				"title" : "card title 1",
				"body" : "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Bestiarum vero nullum iudicium puto. Illa tamen simplicia, vestra versuta. Minime vero istorum quidem, inquit. ",
				"image" : "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__340.jpg"
			},
			{
				"postType": "exc",
				"title" : "card title 1",
				"body" : "Quid est enim aliud esse versutum? Ut aliquid scire se gaudeant? Estne, quaeso, inquam, sitienti in bibendo voluptas? Vide, quantum, inquam, fallare, Torquate.",
			},
			{
				"postType": "ad",
				"title" : "card title 2",
				"body" : "Certe non potest. Vitae autem degendae ratio maxime quidem illis placuit quieta. Prave, nequiter, turpiter cenabat; Gloriosa ostentatio in constituendo summo bono.",
				"image" : "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__340.jpg"
			},
			{
				"postType": "sal",
				"title" : "card title 3",
				"body" : "Videamus animi partes, quarum est conspectus illustrior; Nullus est igitur cuiusquam dies natalis. Nam ante Aristippus, et ille melius. Non est igitur voluptas bonum. At ille pellit, qui permulcet sensum voluptate. Praeteritis, inquit, gaudeo. Atqui reperies, inquit, in hoc quidem pertinacem; Frater et T.",
				"image" : "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__340.jpg"
			},
			{
				"postType": "exc",
				"title" : "card title 3",
				"body" : "Videamus animi partes, quarum est conspectus illustrior; Nullus est igitur cuiusquam dies natalis. Nam ante Aristippus, et ille melius. Non est igitur voluptas bonum. At ille pellit, qui permulcet sensum voluptate. Praeteritis, inquit, gaudeo. Atqui reperies, inquit, in hoc quidem pertinacem; Frater et T.",
				"image" : "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__340.jpg"
			}

		]
	if form.validate_on_submit():
		searchString = form.search.data
		print(searchString)
		return render_template('homepage.html',form=form, searchString=searchString, cards=cards)
	return render_template('homepage.html',form=form, cards=cards)


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