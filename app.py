import os
import shutil
import csv
import sys
import json
import pymongo
import urllib
from flask import Flask,render_template, url_for, flash, redirect, request
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'blah blah blah blah'

client = pymongo.MongoClient("mongodb+srv://ubs:" + urllib.parse.quote('ubs@12345') + "@cluster0.qxrt7.mongodb.net/ubs?retryWrites=true&w=majority")
db = client.University_Bazar_db

class registerForm(FlaskForm):
	firstName = StringField('First Name', validators=[DataRequired()])
	lastName = StringField('Last Name', validators=[DataRequired()])
	emailID = StringField('Email ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit = SubmitField('Submit')

# ROUTES!
@app.route('/',methods=['GET','POST'])
def index():
	form = registerForm()
	if form.validate_on_submit():
		userDataRegistraion = {'FirstName': form.firstName.data, 'LastName': form.lastName.data, 'EmailID': form.emailID.data ,'Password': form.password.data }
		db.userData_db.insert_one(userDataRegistraion).inserted_id
		return render_template('register.html',form=form, user=True)
	return render_template('register.html',form=form,name=None)

@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
	return render_template('404.html',title='404')

@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
	return render_template('500.html',title='500')


port = int(os.getenv('PORT', '3000'))
app.run(host='127.0.0.1', port=port)