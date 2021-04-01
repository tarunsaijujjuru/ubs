import codecs
import os
import shutil
import sys
import time
import urllib
from datetime import datetime
from flask.wrappers import Response

import gridfs
from gridfs.errors import NoFile
import pymongo
from bson import ObjectId
from bson.decimal128 import Decimal128
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    abort,
    make_response,
)
from flask_bootstrap import Bootstrap
from flask_uploads import IMAGES, UploadSet, configure_uploads, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    DecimalField,
    IntegerField,
    PasswordField,
    SelectMultipleField,
    StringField,
    SubmitField,
    validators,
)
from wtforms.fields.core import SelectField
from wtforms.fields.html5 import EmailField, IntegerField
from wtforms.widgets import TextArea

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config["SECRET_KEY"] = "blah blah blah blah"
client = pymongo.MongoClient(
    "mongodb+srv://ubs:"
    + urllib.parse.quote("ubs@12345")
    + "@cluster0.qxrt7.mongodb.net/ubs?retryWrites=true&w=majority"
)

print(client, "MongoCLient")
db = client.University_Bazar_db
fs = gridfs.GridFS(db)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOADED_PHOTOS_DEST"] = os.path.join(basedir, "uploads")

photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB


class registerForm(FlaskForm):
    firstName = StringField("First Name", [validators.DataRequired()])
    lastName = StringField("Last Name", [validators.DataRequired()])
    emailID = EmailField("Email ID", [validators.DataRequired(), validators.Email()])
    password = PasswordField("Password", [validators.DataRequired()])
    submit = SubmitField("submit")


class LoginForm(FlaskForm):
    emailID = StringField("email ID")
    password = PasswordField("Password")
    submit = SubmitField("Submit")


class createPostForm(FlaskForm):
    Title = StringField("Title", [validators.DataRequired()])
    Description = StringField(
        "Description", [validators.DataRequired()], widget=TextArea()
    )
    Image = FileField(
        validators=[FileAllowed(photos, "Image only!"), FileRequired("File was empty!")]
    )
    Clubs = SelectMultipleField("Share To Clubs")
    Users = StringField("Comma separated Emails", widget=TextArea())
    submit = SubmitField("Create")


class createAdForm(FlaskForm):
    Title = StringField("Title", [validators.DataRequired()])
    Description = StringField(
        "Description", [validators.DataRequired()], widget=TextArea()
    )
    Image = FileField(
        validators=[FileAllowed(photos, "Image only!"), FileRequired("File was empty!")]
    )
    submit = SubmitField("Create")


class createSalesForm(FlaskForm):
    Title = StringField("Title", [validators.DataRequired()])
    Description = StringField(
        "Description", [validators.DataRequired()], widget=TextArea()
    )
    Image = FileField(
        validators=[FileAllowed(photos, "Image only!"), FileRequired("File was empty!")]
    )
    price = DecimalField("Enter the price for this item", places=2)
    itemName = StringField("Enter the name of the item")
    submit = SubmitField("Create")


class createPaymentForm(FlaskForm):
    amount = StringField("Amount", render_kw={"readonly": True})
    cardHolderName = StringField("Card Holder Name", [validators.DataRequired()])
    cardNumber = StringField(
        "Card Number",
        [
            validators.DataRequired(),
            validators.Regexp("^\d{16}$", message="Card Number should be of 16 digits"),
        ],
    )
    expirationMonth = IntegerField(
        "Expiration Month",
        [
            validators.NumberRange(
                min=1, max=12, message="Month should be between 01 and 12"
            )
        ],
    )
    expirationYear = IntegerField(
        "Expiration Year",
        [validators.NumberRange(min=2022, message="Year should be greater than 2021")],
    )
    cvv = IntegerField(
        "CVV",
        [
            validators.NumberRange(
                min=100, max=999, message="CVV should be minimum of 3 digits"
            )
        ],
    )
    submit = SubmitField("Confirm Payment")


class searchbar(FlaskForm):
    search = StringField(
        "Search", [validators.DataRequired()], render_kw={"placeholder": "Search"}
    )


class clubsForm(FlaskForm):
    clubName = StringField("Club Name", [validators.DataRequired()])
    description = StringField("Club Description", [validators.DataRequired()])
    submit = SubmitField("submit")


class billing_info_form(FlaskForm):
    streetAddress = StringField("Street Address", [validators.DataRequired()])
    stateAbbr = StringField("State", [validators.DataRequired()])
    zipCode = StringField("Zip Code", [validators.DataRequired()])


class card_deets_form(FlaskForm):
    number = StringField("Card Number", [validators.DataRequired()])
    name = StringField("Name on Card", [validators.DataRequired()])
    expiry = StringField("Expiry", [validators.DataRequired()])
    cvc = StringField("CVV", [validators.DataRequired()])
    streetAddress = StringField("Street Address", [validators.DataRequired()])
    stateAbbr = SelectField(
        "State",
        choices=[
            "AK",
            "AL",
            "AR",
            "AS",
            "AZ",
            "CA",
            "CO",
            "CT",
            "DC",
            "DE",
            "FL",
            "GA",
            "GU",
            "HI",
            "IA",
            "ID",
            "IL",
            "IN",
            "KS",
            "KY",
            "LA",
            "MA",
            "MD",
            "ME",
            "MI",
            "MN",
            "MO",
            "MP",
            "MS",
            "MT",
            "NC",
            "ND",
            "NE",
            "NH",
            "NJ",
            "NM",
            "NV",
            "NY",
            "OH",
            "OK",
            "OR",
            "PA",
            "PR",
            "RI",
            "SC",
            "SD",
            "TN",
            "TX",
            "UM",
            "UT",
            "VA",
            "VI",
            "VT",
            "WA",
            "WI",
            "WV",
            "WY",
        ],
    )
    zipCode = StringField("Zip Code", [validators.DataRequired()])
    billCity = StringField("City", [validators.DataRequired()])
    submit = SubmitField("Make Payment")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = registerForm()
    if request.method == "POST":
        if form.validate_on_submit():
            userData = db.userData_db.find_one({"EmailID": form.emailID.data})
            if userData is None:
                userDataRegistraion = {
                    "FirstName": form.firstName.data,
                    "LastName": form.lastName.data,
                    "EmailID": form.emailID.data,
                    "Password": form.password.data,
                    "Clubs": [],
                }
                db.userData_db.insert_one(userDataRegistraion).inserted_id
                msg = "Registration Succesful Please Login"
                return render_template("register.html", form=form, msg=msg)
            else:
                msg = "User already exists please login"
                return render_template("register.html", form=form, msg=msg)
    return render_template("register.html", form=form)


@app.route("/createPost", methods=["GET", "POST"])
def createPost():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    msg = ""

    form = createPostForm()
    SearchForm = searchbar()
    userData = db.userData_db.find_one({"EmailID": session["EmailID"]})
    postTo = []
    if "Clubs" in userData:
        for club in userData["Clubs"]:
            newTuple = (club, club)
            postTo.append(newTuple)
    form.Clubs.choices = postTo
    if request.method == "POST":
        if form.validate_on_submit():
            searchString = SearchForm.search.data
            print(form.Image.data.content_type)
            file_id = fs.put(
                form.Image.data,
                content_type=form.Image.data.content_type,
                filename=form.Image.data.filename,
            )
            sendToUsers = form.Users.data
            sendToUsersList = sendToUsers.split(",")
            PostData = {
                "Title": form.Title.data,
                "Description": form.Description.data,
                "Image": file_id,
                "Type": "Exchange",
                "TimeStamp": time.time(),
                "postedBy": session["EmailID"],
                "postToClubs": form.Clubs.data,
                "postToUsers": sendToUsersList,
            }

            db.posts.insert_one(PostData).inserted_id
            msg = "Create Post Succesful"

            return render_template(
                "createpost.html",
                msg=msg,
                form=form,
                SearchForm=SearchForm,
                searchString=searchString,
            )
        else:
            msg = "invalid inputs"

    return render_template("createpost.html", form=form, msg=msg, SearchForm=SearchForm)


@app.route("/ad", methods=["GET", "POST"])
def ad():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    msg = ""

    form = createAdForm()
    SearchForm = searchbar()

    if request.method == "POST":
        if form.validate_on_submit():
            searchString = SearchForm.search.data
            file_id = fs.put(
                form.Image.data,
                content_type=form.Image.data.content_type,
                filename=form.Image.data.filename,
            )
            PostData = {
                "Title": form.Title.data,
                "Description": form.Description.data,
                "Image": file_id,
                "Type": "Ad",
                "TimeStamp": time.time(),
                "postedBy": session["EmailID"],
            }
            db.posts.insert_one(PostData).inserted_id
            msg = "Create Post Succesful"
            return render_template(
                "createAd.html",
                msg=msg,
                form=form,
                SearchForm=SearchForm,
                searchString=searchString,
            )
        else:
            msg = "invalid inputs"

    return render_template("createAd.html", form=form, msg=msg, SearchForm=SearchForm)


@app.route("/", methods=["GET", "POST"])
def base():
    return redirect("/login")


# ROUTES!
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    msg = ""
    if form.validate_on_submit():
        emailID = form.emailID.data
        password = form.password.data
        userData = db.userData_db.find_one({"EmailID": emailID})
        if userData is None:
            msg = "User not found"
        else:
            try:
                storedPassword = userData["Password"]
                if storedPassword != password:
                    msg = "password do not match"
                else:
                    session["EmailID"] = userData["EmailID"]
                    session["FirstName"] = userData["FirstName"]
                    session["LastName"] = userData["LastName"]
                    return redirect("/homepage")
            except:
                msg = "some error occured"
        return render_template("login.html", form=form, msg=msg)
    return render_template("login.html", form=form, msg=msg)


@app.route("/clubs", methods=["GET"])
def clubs():
    form = clubsForm()
    searchbarform = searchbar()
    if "EmailID" not in session:
        return redirect("/login")
    clubs = db.clubs.find({})
    user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
    return render_template(
        "clubs.html",
        form=form,
        searchbarform=searchbarform,
        clubs=clubs,
        user_clubs=user_clubs,
    )


@app.route("/createSales", methods=["GET", "POST"])
def createSales():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    msg = ""

    form = createSalesForm()
    SearchForm = searchbar()

    if request.method == "POST":
        if form.validate_on_submit():
            searchString = SearchForm.search.data
            file_id = fs.put(
                form.Image.data,
                content_type=form.Image.data.content_type,
                filename=form.Image.data.filename,
            )
            itemName = form.itemName.data
            price = form.price.data
            salesData = {
                "Title": form.Title.data,
                "Description": form.Description.data,
                "Image": file_id,
                "Type": "Sales",
                "TimeStamp": time.time(),
                "postedBy": session["EmailID"],
                "itemName": itemName,
                "price": Decimal128(price),
            }
            db.sales.insert_one(salesData).inserted_id
            msg = "Create Sales Succesful"
            return render_template(
                "createSales.html",
                msg=msg,
                form=form,
                SearchForm=SearchForm,
                searchString=searchString,
            )
        else:
            msg = "invalid inputs"

    return render_template(
        "createSales.html", form=form, msg=msg, SearchForm=SearchForm
    )


@app.route("/viewPaymentForm", methods=["GET", "POST"])
def viewPaymentForm():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    searchbarform = searchbar()
    form = createPaymentForm()
    msg = ""

    if request.method == "GET":
        id = request.args.get("id")
        amount = db.sales.find_one({"_id": ObjectId(id)})["price"]
        form.amount.data = "$" + str(amount)
        session["itemId"] = str(ObjectId(id))
    else:
        if form.validate_on_submit():
            db.payments.insert_one(
                {
                    "paidBy": session["EmailID"],
                    "amount": form.amount.data,
                    "itemId": session["itemId"],
                    "paidAt": datetime.now(),
                }
            )
            session.pop("itemId", None)
            msg = "Payment Successful. Redirect to purchase history tab for more information"
            return render_template(
                "payment_form.html", form=form, msg=msg, searchbarform=searchbarform
            )

    return render_template(
        "payment_form.html", form=form, msg=msg, searchbarform=searchbarform
    )


@app.route("/purchaseHistory", methods=["GET"])
def purchaseHistory():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    searchbarform = searchbar()

    purchases = []
    payments = db.payments.find({})

    for payment in payments:
        purchase = {}
        item = db.sales.find_one({"_id": ObjectId(payment["itemId"])})
        purchase["itemName"] = item["itemName"]
        purchase["itemCost"] = payment["amount"]
        purchase["date"] = payment["paidAt"].strftime("%Y-%m-%d")
        purchase['Image'] = item['Image']
        purchases.append(purchase)

    return render_template(
        "purchaseHistory.html", purchases=purchases, searchbarform=searchbarform
    )


@app.route("/viewSales", methods=["GET", "POST"])
def viewSales():
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")
    searchbarform = searchbar()

    if searchbarform.validate_on_submit():
        searchString = searchbarform.search.data
        print(searchString)
        return render_template(
            "viewSales.html", searchbarform=searchbarform, searchString=searchString
        )
    cards = []
    total = db.sales.count_documents({})
    print("Total Document", total)
    documents = db.sales.find({})
    counter = 1
    card = []
    for doc in documents:
        newEntry = {}
        newEntry["title"] = doc["Title"]
        # image = fs.get(doc["Image"])
        # print("View Sales Image ID:", doc["Image"], image.content_type)
        # base64_data = codecs.encode(image.read(), "base64")
        # image = base64_data.decode("utf-8")
        # newEntry["image"] = image
        newEntry['imgId'] = doc['Image']
        newEntry["body"] = doc["Description"]
        newEntry["ID"] = doc["_id"]
        newEntry["price"] = doc["price"]
        newEntry["itemName"] = doc["itemName"]

        card.append(newEntry)
        if (counter % 3 == 0) or (counter == total):
            cards.append(card)
            card = []
        counter += 1
    return render_template("viewSales.html", searchbarform=searchbarform, cards=cards)


@app.route("/create_club", methods=["POST"])
def create_club():
    form = clubsForm()
    searchbarform = searchbar()
    if "EmailID" not in session:
        return redirect("/login")
    clubs = db.clubs.find({})
    if form.validate_on_submit():
        club_name = form.clubName.data
        description = form.description.data
        club = db.clubs.find_one({"name": club_name})
        user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
        if club is None:
            db.clubs.insert_one(
                {
                    "name": club_name,
                    "users": [session["EmailID"]],
                    "description": description,
                }
            )
            user_clubs.append(club_name)
            db.userData_db.update_one(
                {"EmailID": session["EmailID"]}, {"$set": {"Clubs": user_clubs}}
            )
            msg = "Club is created"
            clubs = db.clubs.find({})
        else:
            msg = "Club already exists. Please choose other name"
        return render_template(
            "clubs.html",
            form=form,
            searchbarform=searchbarform,
            clubs=clubs,
            user_clubs=user_clubs,
            msg=msg,
        )
    user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
    return render_template(
        "clubs.html",
        form=form,
        searchbarform=searchbarform,
        clubs=clubs,
        user_clubs=user_clubs,
    )


@app.route("/join_club", methods=["POST"])
def join_club():

    form = clubsForm()
    searchbarform = searchbar()
    if "EmailID" not in session:
        return redirect("/login")

    if request.method == "POST":
        club_name = request.get_json(force=True)["club_name"]
        users = db.clubs.find_one({"name": club_name})["users"]
        users.append(session["EmailID"])
        db.clubs.update_one({"name": club_name}, {"$set": {"users": users}})

        user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
        user_clubs.append(club_name)
        db.userData_db.update_one(
            {"EmailID": session["EmailID"]}, {"$set": {"Clubs": user_clubs}}
        )

        msg = "Joined the club successfully"
        clubs = db.clubs.find({})
        return render_template(
            "clubs.html",
            form=form,
            searchbarform=searchbarform,
            clubs=clubs,
            user_clubs=user_clubs,
            msg=msg,
        )
    clubs = db.clubs.find({})
    return render_template(
        "clubs.html", form=form, searchbarform=searchbarform, clubs=clubs, msg=""
    )


@app.route("/leave_club", methods=["POST"])
def leave_club():
    form = clubsForm()
    searchbarform = searchbar()
    if "EmailID" not in session:
        return redirect("/login")

    if request.method == "POST":
        club_name = request.get_json(force=True)["club_name"]
        users = db.clubs.find_one({"name": club_name})["users"]
        users.remove(session["EmailID"])
        if len(users) == 0:
            db.clubs.delete_one({"name": club_name})
            msg = "Left and the club is deleted due to zero users"
        else:
            db.clubs.update_one({"name": club_name}, {"$set": {"users": users}})
            msg = "Left the club successfully"

        user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
        user_clubs.remove(club_name)
        db.userData_db.update_one(
            {"EmailID": session["EmailID"]}, {"$set": {"Clubs": user_clubs}}
        )
        clubs = db.clubs.find({})
        return render_template(
            "clubs.html",
            form=form,
            searchbarform=searchbarform,
            clubs=clubs,
            user_clubs=user_clubs,
            msg=msg,
        )
    clubs = db.clubs.find({})
    return render_template(
        "clubs.html", form=form, searchbarform=searchbarform, clubs=clubs, msg=""
    )


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("EmailID", None)
    session.pop("FirstName", None)
    session.pop("LastName", None)
    print(session)
    return redirect("/login")


@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    if "EmailID" not in session:
        return redirect("/login")
    if request.method == "POST":
        if request.form["deletePost"]:
            id = request.form["deletePost"]
            db.posts.delete_one({"_id": ObjectId(id)})

    searchbarform = searchbar()
    # Checking session
    print(session)

    cards = []
    user_clubs = db.userData_db.find_one({"EmailID": session["EmailID"]})["Clubs"]
    total = db.posts.count_documents({"postToClubs": {"$in": user_clubs}})
    print("Total Document", total)
    typequery = ["Exchange", "Ad"]
    documents = db.posts.find(
        {
            "$and": [
                {
                    "$or": [
                        {"postedBy": session["EmailID"]},
                        {"postToUsers": [session["EmailID"]]},
                        {"postToClubs": {"$in": user_clubs}},
                        {"Type": {"$in": typequery}},
                    ]
                },
                {"Type": {"$in": typequery}},
            ]
        }
    )
    for doc in documents:
        print(doc)
        newEntry = {}
        newEntry["postType"] = doc["Type"]
        newEntry["title"] = doc["Title"]
        email = doc["postedBy"]
        Firstname = db.userData_db.find_one({"EmailID": email})["FirstName"]
        newEntry["FirstName"] = Firstname
        # image = fs.get(doc["Image"])
        # print(image.content_type, image.filename, doc["Image"])
        # base64_data = codecs.encode(image.read(), "base64")
        # image = base64_data.decode("utf-8")
        # newEntry["image"] = image
        newEntry["imgId"] = doc["Image"]
        newEntry["body"] = doc["Description"]
        newEntry["ID"] = doc["_id"]
        if doc["postedBy"] == session["EmailID"]:
            newEntry["deleteBtn"] = 1
        else:
            newEntry["deleteBtn"] = 0
        cards.append(newEntry)

    if searchbarform.validate_on_submit():
        searchString = searchbarform.search.data
        # print(searchString)
        return render_template(
            "homepage.html",
            searchbarform=searchbarform,
            searchString=searchString,
            cards=cards,
        )

    return render_template(
        "homepage.html", searchbarform=searchbarform, cards=cards
    )  # image=image


@app.route("/messages", methods=["GET"])
def messages():
    form = searchbar()

    # Checking session
    print(session)

    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")

    if form.validate_on_submit():
        searchString = form.search.data
        print(searchString)
        return render_template("messages.html", form=form, searchString=searchString)
    return render_template("messages.html", form=form)


@app.route("/payment/<buy_id>", methods=["GET", "POST"])
def payment_portal(buy_id):
    if "EmailID" not in session:
        print("Redirect")
        return redirect("/login")

    form = billing_info_form()

    ccform = card_deets_form()

    return render_template("payment_prompt.html", form=form, ccform=ccform)


@app.route("/file/<objectId>", methods=["GET"])
def get_file(objectId):
    try:
        file = fs.get(ObjectId(objectId))
        resp = make_response(file.read())
        resp.mimetype = file.content_type
        return resp
    except (NoFile, AttributeError):
        abort(404)


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return render_template("404.html", title="404")


port = int(os.getenv("PORT", "3000"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=port, debug=True)
