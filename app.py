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
					return render_template('homepage.html', form=form)
			except:
				msg = "some error occured"
		return render_template('login.html',form=form,msg=msg)
	return render_template('login.html',form=form,msg=msg)

@app.route('/homepage',methods=['GET','POST'])
def homepage():
	form = searchbar()
	if form.validate_on_submit():
		searchString = form.search.data
		print(searchString)
		return render_template('homepage.html',form=form, searchString=searchString)
	return render_template('homepage.html',form=form)


@app.route('/messages',methods=['GET'])
def messages():
	form = searchbar()
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

if __name__ == "__main__"
	app.run(host='127.0.0.1', port=port)