from bson import ObjectId
from flask import *
from flask_pymongo import PyMongo
from flask_moment import Moment
from datetime import datetime

fl = Flask("study")
moment = Moment(fl)
fl.config["SECRET_KEY"] = "RANDOMkey"
fl.config['MONGO_URI'] = "mongodb://localhost:27017/study-db"
mongo = PyMongo(fl)

@fl.template_filter()
def format_date(value):
    value = datetime.strptime(value,"%Y-%m-%d").date()
    return value.strftime('%m/%d/%y')
@fl.template_filter()
def format_time(value):
    value = datetime.strptime(value,"%H:%M").time()
    return value.strftime('%I:%M %p')


@fl.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)


@fl.route("/", methods=["GET", "POST"])
def register():
    if "info" in session:
        flash("You are already logged in.")
        return redirect("/home")
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        exist = mongo.db.loginInfo.find_one({"email": request.form['email']})
        if exist is None:
            doc = {}
            for item in request.form:
                doc[item] = request.form[item]
            mongo.db.loginInfo.insert_one(doc)
            print("new acc created")
            flash("Account created successfully!")
            return redirect("/login")
        else:
            flash("This email has already been used!")
            return redirect("/")


@fl.route("/login", methods=["GET", "POST"])
def login():
    if "info" in session:
        flash("You are already logged in.")
        return redirect("/home")
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        doc = {"email": request.form["email"],
               "password": request.form["password"]}
        exist = mongo.db.loginInfo.find_one(doc)
        if exist is None:
            flash(
                'The information you entered does not match our records. Please try again.')
            return redirect("/login")
        else:
            session["info"] = {'firstName': exist['firstName'], 'lastName': exist['lastName'],
                               'email': exist['email'], 'time': datetime.utcnow()}
            return redirect("/home")


@fl.route("/home", methods=["GET", "POST"])
def home():
    if "info" not in session:
        flash("Error: You must log in before accessing this page.")
        return redirect("/login")
    if request.method == "GET":
        myPostsQuery = {'user': session['info']['email']}
        signUpQuery = {'signups': {'$in': [ session['info']['email'] ]}}
        allPosts = list(mongo.db.posts.find().sort('time', -1))
        myPosts = list(mongo.db.posts.find(myPostsQuery).sort('time', -1))
        mySignUps = list(mongo.db.posts.find(signUpQuery).sort('time', -1))

        openPosts = []

        for post in allPosts:
            if post in myPosts:
                continue
            if post in mySignUps:
                continue
            if int(post["max-capacity"]) < len(post["signups"]):
                continue
            openPosts.append(post)
        return render_template("home.html", allPosts=openPosts, myPosts=myPosts, mySignUps=mySignUps)
    elif request.method == "POST":
        global searchData
        for item in request.form:
            if request.form['search'] != "":
                search = request.form['search']
                searchData = searching(search)
                return redirect("/viewSearch")
            else:
                return redirect("/home")


@fl.route("/view", methods=["GET", "POST", "SEARCH"])
def view():

    if request.method == "GET":
        return render_template("view.html", allPosts=allData)
    elif request.method == "POST":
        global searchData
        for item in request.form:
            if request.form['search'] != "":
                search = request.form['search']
                searchData = searching(search)
                return redirect("/viewSearch")
            else:
                return redirect("/home")

def searching(search):
    myPostsQuery = {'user': session['info']['email']}
    signUpQuery = {'signups': {'$in': [session['info']['email']]}}
    allPosts = list(mongo.db.posts.find().sort('time', -1))
    myPosts = list(mongo.db.posts.find(myPostsQuery).sort('time', -1))
    mySignUps = list(mongo.db.posts.find(signUpQuery).sort('time', -1))

    allData = []

    for post in allPosts:
        if post in myPosts:
            continue
        if post in mySignUps:
            continue
        if int(post["max-capacity"]) < len(post["signups"]):
            continue
        allData.append(post)

    newdata = []
    for data in allData:
        data['title'] = data['title'].lower()
        data['description'] = data['description'].lower()
        newdata.append(data)
    searchResults = []
    for data in newdata:
        if search.lower() in data['title']:
            searchResults.append(data)
        if search.lower() in data['description']:
            searchResults.append(data)
    return searchResults


@fl.route("/viewSearch", methods=["GET", "POST"])
def viewSearch():
    if request.method == "GET":
        return render_template("viewsearch.html", allSearches=searchData)
    if request.method == "POST":
        return redirect("/home")


@fl.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("create.html")
    elif request.method == "POST":
        flash("Successfully created a post!")

        for item in request.form:
            title = request.form["title"]
            date = request.form["date"]
            studytime = request.form["time"]
            subject = request.form["subject"]
            location = request.form["location"]
            description = request.form["description"]
            maximum = request.form["maximum"]
            signups = []

        entry = {
            "title": title,
            "date": date,
            "studytime": studytime,
            "subject": subject,
            "location": location,
            "description": description,
            "user": session["info"]["email"],
            "name": session["info"]["firstName"] + " "+ session["info"]["lastName"],
            "time": datetime.utcnow(),
            "max-capacity": maximum,
            "signups": signups
        }

        mongo.db.posts.insert_one(entry)

        return redirect("/home")

@fl.route("/signup/<id>")
def signup(id):
    mongo.db.posts.update_one( {"_id":ObjectId(id)},{"$push":{'signups':session["info"]["email"]}})
    flash("Signup successful!")
    return redirect("/home")

@fl.route("/optout/<id>")
def optout(id):
    mongo.db.posts.update_one({'_id':ObjectId(id)},{'$pull':{'signups':session["info"]["email"]}})
    flash("You have opted out of this study session.")
    return redirect("/home")
@fl.route("/delete/<id>")
def delRoute(id):
    # ids are not strings they are ObjectId('')
    # html has all strings
    flash("Deleted")
    delItem = mongo.db.posts.find_one({'_id': ObjectId(id)})
    mongo.db.posts.delete_one(delItem)
    return redirect("/home")




@fl.route("/logout")
def out():
    session.clear()
    flash("You have been logged out.")
    return redirect("/login")


@fl.errorhandler(404)
def noPage(error):
    # error starting with 2 ex: 200 is ok, 302 is redirect, 404 is not found (status codes)
    return render_template("error.html", error=error)


fl.run(debug=True)
