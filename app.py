import shutil
import sys
import os
import pymongo
import json

import urllib
from flask import Flask,render_template, url_for, flash, redirect, request
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
	return render_template('base.html')

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
					msg = "logged in successfully"
			except:
				msg = "some error occured"


		return render_template('login.html',form=form,msg=msg)
	return render_template('login.html',form=form,msg=msg)



port = int(os.getenv('PORT', '3000'))
app.run(host='127.0.0.1', port=port)