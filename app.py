import os
import shutil
import csv
import sys
from flask import Flask,render_template, url_for, flash, redirect, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, SubmitField, SelectField, validators
from wtforms.validators import DataRequired

app = Flask(__name__)
bootstrap = Bootstrap(app)

# Configurations
app.config['SECRET_KEY'] = 'blah blah blah blah'

class NameForm(FlaskForm):
	name = StringField('Name', default="Bruce Springsteen")
	submit = SubmitField('Submit')

class searchbar(FlaskForm):
	search = StringField('Search' ,[validators.DataRequired()], render_kw={"placeholder": "Search"})
	# submit = SubmitField('Search')

# ROUTES!
@app.route('/',methods=['GET','POST'])
def index():
	form = NameForm()
	if form.validate_on_submit():
		name = form.name.data
		return render_template('index.html',form=form,name=name)
	return render_template('index.html',form=form,name=None)

@app.route('/help')
def help():
	text_list = []
	# Python Version
	text_list.append({
		'label':'Python Version',
		'value':str(sys.version)})
	# os.path.abspath(os.path.dirname(__file__))
	text_list.append({
		'label':'os.path.abspath(os.path.dirname(__file__))',
		'value':str(os.path.abspath(os.path.dirname(__file__)))
		})
	# OS Current Working Directory
	text_list.append({
		'label':'OS CWD',
		'value':str(os.getcwd())})
	# OS CWD Contents
	label = 'OS CWD Contents'
	value = ''
	text_list.append({
		'label':label,
		'value':value})
	return render_template('help.html',text_list=text_list,title='help')


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

@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
	return render_template('500.html',title='500')

port = int(os.getenv('PORT', '3000'))
app.run(host='0.0.0.0', port=port)