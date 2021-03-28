import codecs
import shutil
import sys
import os
import pymongo
import json
import urllib
import gridfs
import time
from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from bson.objectid import ObjectId
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
client = pymongo.MongoClient("mongodb+srv://ubs:" + urllib.parse.quote(
    'ubs@12345') + "@cluster0.qxrt7.mongodb.net/ubs?retryWrites=true&w=majority")
db = client.University_Bazar_db
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'uploads')

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB


class registerForm(FlaskForm):
    firstName = StringField('First Name', [validators.DataRequired()])
    lastName = StringField('Last Name', [validators.DataRequired()])
    emailID = EmailField('Email ID', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('submit')


class LoginForm(FlaskForm):
    emailID = StringField('email ID')
    password = PasswordField('Password')
    submit = SubmitField('Submit')


class createPostForm(FlaskForm):
    Title = StringField('Title', [validators.DataRequired()])
    Type = SelectField(
        'Type',
        choices=[('Exchange', 'Exchange'), ('Sales', 'Sales'), ('Ad', 'Ad')]
    )
    Description = StringField('Description', [validators.DataRequired()], widget=TextArea())
    Image = FileField(validators=[FileAllowed(photos, 'Image only!'), FileRequired('File was empty!')])
    Clubs = SelectMultipleField('Share To Clubs')
    Users = StringField('Comma separated Emails', widget=TextArea())
    submit = SubmitField('Create')


class searchbar(FlaskForm):
    search = StringField('Search', [validators.DataRequired()], render_kw={"placeholder": "Search"})


class createpost(FlaskForm):
    title = StringField('Title', [validators.DataRequired()])
    posttype = SelectField(
        'posttype',
        choices=[('Exchange', 'Exchange'), ('Sales', 'Sales'), ('Ad', 'Ad')]
    )
    description = StringField('description', [validators.DataRequired()], widget=TextArea())
    shareTo = SelectField('Share To', [validators.DataRequired()])
    submit = SubmitField('Create')


class clubsForm(FlaskForm):
    clubName = StringField('Club Name', [validators.DataRequired()])
    description = StringField('Club Description', [validators.DataRequired()])
    submit = SubmitField('submit')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = registerForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            userData = db.userData_db.find_one({'EmailID': form.emailID.data})
            if userData is None:
                userDataRegistraion = {'FirstName': form.firstName.data, 'LastName': form.lastName.data,
                                       'EmailID': form.emailID.data, 'Password': form.password.data}
                db.userData_db.insert_one(userDataRegistraion).inserted_id
                msg = "Registration Succesful Please Login"
                return render_template('register.html', form=form, msg=msg)
            else:
                msg = "User already exists please login"
                return render_template('register.html', form=form, msg=msg)
    return render_template('register.html', form=form)


@app.route('/createPost', methods=['GET', 'POST'])
def createPost():
    if (('EmailID' not in session)):
        print('Redirect')
        return redirect('/login')
    msg = ""

    form = createPostForm()
    SearchForm = searchbar()
    userData = db.userData_db.find_one({'EmailID': session['EmailID']})
    postTo = []
    if 'Clubs' in userData:
        for club in userData['Clubs']:
            newTuple = (club, club)
            postTo.append(newTuple)
    form.Clubs.choices = postTo
    print(form.Clubs.choices)
    if request.method == 'POST':
        if form.validate_on_submit():
            searchString = SearchForm.search.data
            fs = gridfs.GridFS(db)
            file_id = fs.put(form.Image.data, filename=form.Image.data.filename)
            sendToUsers = form.Users.data
            paymentRequired = False
            if form.Type.data == 'Sales':
                paymentRequired = True
            sendToUsersList = sendToUsers.split(',')
            PostData = {'Title': form.Title.data,
                        'Type': form.Type.data,
                        'Description': form.Description.data,
                        'Image': file_id,
                        'TimeStamp': time.time(),
                        'postedBy': session['EmailID'],
                        'postToClubs': form.Clubs.data,
                        'PaymentRequired': paymentRequired,
                        'postToUsers': sendToUsersList}
            db.posts.insert_one(PostData).inserted_id
            msg = "Create Post Succesful"

            # image_data = fs.get(ObjectId('60446568ab7abf152435dd5d'))
            # image_data = image_data.read()
            return render_template('createpost.html', msg=msg, form=form, SearchForm=SearchForm,
                                   searchString=searchString)
        else:
            msg = "invalid inputs"

    return render_template('createpost.html', form=form, msg=msg, SearchForm=SearchForm)


@app.route('/', methods=['GET', 'POST'])
def base():
    return redirect('/login')


# ROUTES!
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    msg = ""
    if form.validate_on_submit():
        emailID = form.emailID.data
        password = form.password.data
        userData = db.userData_db.find_one({'EmailID': emailID})
        if (userData is None):
            msg = "User not found"
        else:
            try:
                storedPassword = userData["Password"]
                if (storedPassword != password):
                    msg = "password do not match"
                else:
                    session['EmailID'] = userData['EmailID']
                    session['FirstName'] = userData['FirstName']
                    session['LastName'] = userData['LastName']
                    return redirect('/homepage')
            except:
                msg = "some error occured"
        return render_template('login.html', form=form, msg=msg)
    return render_template('login.html', form=form, msg=msg)


@app.route('/clubs', methods=['GET'])
def clubs():
    form = clubsForm()
    searchbarform = searchbar()
    if (('EmailID' not in session)):
        return redirect('/login')

    clubs = db.clubs.find({})
    user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']

    return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, user_clubs=user_clubs)


@app.route('/create_club', methods=['POST'])
def create_club():
    form = clubsForm()
    searchbarform = searchbar()
    if (('EmailID' not in session)):
        return redirect('/login')

    clubs = db.clubs.find({})

    if form.validate_on_submit():
        club_name = form.clubName.data
        description = form.description.data
        club = db.clubs.find_one({'name': club_name})
        user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']
        # print("club",user_clubs)
        if club is None:
            db.clubs.insert_one({'name': club_name, 'users': [session['EmailID']], 'description': description})
            user_clubs.append(club_name)
            db.userData_db.update_one({'EmailID': session['EmailID']}, {'$set': {'Clubs': user_clubs}})
            msg = 'Club is created'
            clubs = db.clubs.find({})
        else:
            msg = 'Club already exists. Please choose other name'
        return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, user_clubs=user_clubs,
                               msg=msg)
    user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']
    return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, user_clubs=user_clubs)


@app.route('/join_club', methods=['POST'])
def join_club():
    form = clubsForm()
    searchbarform = searchbar()
    if (('EmailID' not in session)):
        return redirect('/login')

    if request.method == 'POST':
        club_name = request.get_json(force=True)['club_name']
        users = db.clubs.find_one({'name': club_name})['users']
        users.append(session['EmailID'])
        db.clubs.update_one({'name': club_name}, {'$set': {'users': users}})

        user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']
        user_clubs.append(club_name)
        db.userData_db.update_one({'EmailID': session['EmailID']}, {'$set': {'Clubs': user_clubs}})

        msg = "Joined the club successfully"
        clubs = db.clubs.find({})
        return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, user_clubs=user_clubs,
                               msg=msg)
    clubs = db.clubs.find({})
    return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, msg="")


@app.route('/leave_club', methods=['POST'])
def leave_club():
    form = clubsForm()
    searchbarform = searchbar()
    if (('EmailID' not in session)):
        return redirect('/login')

    if request.method == 'POST':
        club_name = request.get_json(force=True)['club_name']
        users = db.clubs.find_one({'name': club_name})['users']
        users.remove(session['EmailID'])
        if len(users) == 0:
            db.clubs.delete_one({'name': club_name})
            msg = "Left and the club is deleted due to zero users"
        else:
            db.clubs.update_one({'name': club_name}, {'$set': {'users': users}})
            msg = "Left the club successfully"

        user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']
        user_clubs.remove(club_name)
        db.userData_db.update_one({'EmailID': session['EmailID']}, {'$set': {'Clubs': user_clubs}})
        clubs = db.clubs.find({})
        return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, user_clubs=user_clubs,
                               msg=msg)
    clubs = db.clubs.find({})
    return render_template('clubs.html', form=form, searchbarform=searchbarform, clubs=clubs, msg="")


@app.route('/logout', methods=['GET'])
def logout():
    session.pop("EmailID", None)
    session.pop("FirstName", None)
    session.pop("LastName", None)
    print(session)
    return redirect('/login')


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    print("here again")
    if request.method=='POST':
        if request.form['deletePost']:
            id = request.form['deletePost']
            # print(id)
            db.posts.delete_one({'_id': ObjectId(id)})
            # print("deleted")


    searchbarform = searchbar()
    createpostform = createpost()
    # Checking session
    print(session)
    fs = gridfs.GridFS(db)

    if (('EmailID' not in session)):
        print('Redirect')
        return redirect('/login')


    cards = []
    user_clubs = db.userData_db.find_one({'EmailID': session['EmailID']})['Clubs']
    total = db.posts.count_documents({"postToClubs": {"$in": user_clubs}})
    print("Total Document", total)
    typequery = ["Exchange", "Ad"]
    documents = db.posts.find(
        {"$and": [{"$or": [{"postedBy": session['EmailID']}, {"postToUsers": [session['EmailID']]},
                           {"postToClubs": {"$in": user_clubs}}, {"Type": {"$in": typequery}}]},
                  {"Type": {"$in": typequery}}]})
    for doc in documents:
        print(doc)
        newEntry = {}
        newEntry["postType"] = doc['Type']
        newEntry["title"] = doc['Title']
        email = doc['postedBy']
        Firstname = db.userData_db.find_one({'EmailID':email})['FirstName']
        print(Firstname)
        newEntry['FirstName'] = Firstname
        image = fs.get(doc['Image'])
        base64_data = codecs.encode(image.read(), 'base64')
        image = base64_data.decode('utf-8')
        newEntry["image"] = image
        newEntry["body"] = doc['Description']
        newEntry["ID"] = doc['_id']
        if doc['postedBy'] == session['EmailID']:
            newEntry["deleteBtn"] = 1
        else:
            newEntry["deleteBtn"] = 0
        cards.append(newEntry)

    if searchbarform.validate_on_submit():
        searchString = searchbarform.search.data
        # print(searchString)
        return render_template('homepage.html', searchbarform=searchbarform,
                               searchString=searchString, cards=cards)

    return render_template('homepage.html', searchbarform=searchbarform,
                           cards=cards)  # image=image


@app.route('/messages', methods=['GET'])
def messages():
    form = searchbar()

    # Checking session
    print(session)

    if (('EmailID' not in session)):
        print('Redirect')
        return redirect('/login')

    if form.validate_on_submit():
        searchString = form.search.data
        print(searchString)
        return render_template('messages.html', form=form, searchString=searchString)
    return render_template('messages.html', form=form)


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return render_template('404.html', title='404')


port = int(os.getenv('PORT', '3000'))

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=port, debug=True)
