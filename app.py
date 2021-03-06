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

class clubsForm(FlaskForm):
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

@app.route('/clubs', methods=['GET'])
def clubs():
	form = clubsForm()

	if(('EmailID' not in session)):
		return redirect('/login')

	clubs = db.clubs.find({})
	user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['clubs']
	return render_template('clubs.html', form=form, clubs=clubs, user_clubs=user_clubs)

@app.route('/create_club', methods=['POST'])
def create_club():
	form = clubsForm()

	if(('EmailID' not in session)):
		return redirect('/login')

	clubs = db.clubs.find({})

	if form.validate_on_submit():
		club_name = form.club_name.data
		club = db.clubs.find_one({'name': club_name})

		if club is None:
			db.clubs.insert_one({'name': club_name, 'users': [session['EmailID']]})
			msg = 'Club is created'
		else:
			msg = 'Club already exists. Please choose other name'
		return render_template('clubs.html', form=form, clubs=clubs, msg=msg)
	return render_template('clubs.html', form=form, clubs=clubs)

@app.route('/join_club', methods=['POST'])
def join_club():
	form = clubsForm()

	if(('EmailID' not in session)):
		return redirect('/login')

	if form.validate_on_submit():
		club_name = form.club_name.data
		users = db.clubs.find_one({'name': club_name})['users']
		users.append(session['EmailID'])
		db.clubs.update_one({'name': club_name}, {'$set': {'users': users}})
		msg = "Joined the club successfully"
	clubs = db.clubs.find({})
	return render_template('clubs.html', form=form, clubs=clubs, msg=msg)

@app.route('/leave_club', methods=['POST'])
def leave_club():
	form = clubsForm()

	if(('EmailID' not in session)):
		return redirect('/login')

	if form.validate_on_submit():
		club_name = form.club_name.data
		users = db.clubs.find_one({'name': club_name})['users']
		users.remove(session['EmailID'])
		if len(users) == 0:
			db.clubs.delete_one({'name': club_name})
			msg = "Left and the club is deleted due to zero users"
		else:
			db.clubs.update_one({'name': club_name}, {'$set': {'users': users}})
			msg = "Left the club successfully"
	clubs = db.clubs.find({})
	return render_template('clubs.html', form=form, clubs=clubs, msg=msg)

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