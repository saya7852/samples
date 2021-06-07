import os
import re
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from time import sleep

# --- this is the main program that runs the webtool ---

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["SECRET_KEY"] = '4SW0anVZVQ45dF14UEU1Ig'

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wordlist1.db")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/")
def index():

    # TODO: add introductory contents for the new/potential users
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    responses = []

    # Forget any user_id
    session.clear()

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html", responses=responses)

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure username was submitted
        if not request.form.get("username"):
            responses.append('Please enter username')

        # Ensure password was submitted
        if not request.form.get("password"):
            responses.append('Please enter password')

        else:
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=request.form.get("username"))

             # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                responses.append('Incorrect username or password')

        if not responses:

            # Remember which user has logged in
            session["user_id"] = rows[0]["userID"]

            # Redirect user to /generate
            return redirect("/generate")

        else:
            return render_template("login.html", responses=responses)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    """search for phrases"""

    # TODO: add functionality to allow user to specify the number of output samples
    # TODO: add grade/difficulty level & other filters


    responses = []

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":

        user = session["user_id"]

        # verify if user registration is completed - else error response
        check_if_in = db.execute("SELECT * FROM users WHERE userID = :user AND registered = 'Y'", user=user)

        if len(check_if_in) == 0:
            responses.append('Your registration is not complete.  Please register first.')
            return render_template("register.html", responses=responses)

        else:
            return render_template("generate.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        target = request.form.get("target")

        if target == None:
            responses.append('Please enter target word(s).')

        else:
            if not responses:

                # change input to uppercase
                t = target.upper()

                # TODO: modify to make the output more random (ORDER BY RANDOM() does not seem to do much)
                h = db.execute("SELECT element, hElement, cID FROM corpus2 WHERE elementID IN (SELECT eID FROM sentences WHERE sID IN (SELECT s_ID FROM maxW WHERE v_ID = (SELECT vID FROM vWords WHERE vWord = :t) ORDER BY RANDOM()))", t=t)

                # error response if search resulted none
                if len(h) < 1:
                    responses.append('Sorry!  We could not find that word!')
                    return render_template("generate.html", responses=responses)

                ph1 = []
                ph2 = []
                ph3 = []
                count = 0

                # iterate h to output 3 sample phrases
                for i in h:

                    if count < 4:

                        c = i["cID"]
                        word = i["element"]

                        # handle markers
                        if word == "SSSSS":
                            if i["hElement"] == None:
                                word = ' '

                                # fetch corpus data
                                cor = db.execute("SELECT cDetails, source FROM corpora WHERE cID = :c", c=c)
                                corpus = cor[0]["cDetails"]
                                source = cor[0]["source"]
                                count += 1

                            # output characters
                            else:
                                word = i["hElement"]

                        # output words lead by a space
                        else:
                            word = ' ' + i["element"]


                        separator = ''

                    # TODO: change output to sentense case & highlight targets within
                    # TODO: capitalize proper nouns - add boolean in iteration above
                    if count == 1:
                        ph1.append(word.lower())
                        phrase = separator.join(ph1)
                    if count == 2:
                        ph2.append(word.lower())
                        phrase2 = separator.join(ph2)
                    if count == 3:
                        ph3.append(word.lower())
                        phrase3 = separator.join(ph3)

                # output results
                return render_template("display.html", target=target, phrase=phrase, phrase2=phrase2, phrase3=phrase3, responses=responses, corpus=corpus, source=source)



@app.route("/register", methods=["GET", "POST"])
def register():
    """registration part 1 - login info"""

    responses = []
    if request.method == "GET":
        return render_template("register.html", responses=responses)

    else:

        # if user submits input, verify name is provided and it's unique
        found_name = db.execute("SELECT * FROM users WHERE username = :newname", newname=request.form.get("newname"))

        if len(found_name) != 0:
            responses.append('That username is taken - please pick another')

        else:

            newname=request.form.get("newname")
            # verify password is provided and it matches with "confirm"
            if request.form.get("password") != request.form.get("confirm"):
                responses.append('The passwords do not match')

            # email verification code from: https://www.scottbrady91.com/Email-Verification/Python-Email-Verification-Script
            checkEmail = request.form.get("email")
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', checkEmail)

            if match == None:
                responses.append('Please enter a valid email address')

            else:
                email = checkEmail
                # hash the password to get pw_hash & add both username and pw_hash to table "users"
                newname = request.form.get("newname")
                pw_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
                db.execute("INSERT INTO users (username, hash, email) VALUES (:newname, :pw_hash, :email)", newname=newname, pw_hash=pw_hash, email=email)

                rows = db.execute("SELECT * FROM users WHERE username = :newname", newname=newname)

                # Remember the user id
                session["user_id"] = rows[0]["userID"]

                return render_template("pagetwo.html", responses=responses)


    return render_template("register.html", responses=responses)

@app.route("/pagetwo", methods=["GET", "POST"])
def pagetwo():
    """registration part 2 - user profile"""

    responses = []

    if request.method == "GET":
        return render_template("pagetwo.html", responses=responses)

    else:
        user = session["user_id"]
        check_p_one = db.execute("SELECT * FROM users WHERE userID = :user", user=user)

        if check_p_one == None:
            responses.append('Please complete your login information to register.')

       # create a new table "profiles" if not there & insert user_ID and actionType "registered"
        db.execute("CREATE TABLE IF NOT EXISTS profiles (user_ID INT, u_role TEXT, r_info TEXT, pr_lang TEXT, l_info TEXT, edu_lang TEXT, ed_info TEXT, origin TEXT, rmks VARCHAR(255), FOREIGN KEY (user_id) REFERENCES users (userID))")

        # get data from user input
        u_role = request.form.get("u_role")
        r_info = request.form.get("r_info")
        pr_lang = request.form.get("pr_lang")
        l_info = request.form.get("l_info")
        edu_lang = request.form.get("edu_lang")
        ed_info = request.form.get("ed_info")
        origin = request.form.get("origin")
        rmks = request.form.get("rmks")

        # insert data into profiles
        db.execute("INSERT INTO profiles (u_role, pr_lang, edu_lang, origin, rmks, user_ID) VALUES (:u_role, :pr_lang, :edu_lang, :origin, :rmks, (SELECT userID FROM users WHERE userID = :user))",
                   u_role=u_role, pr_lang=pr_lang, edu_lang=edu_lang, origin=origin, rmks=rmks, user=user)

        if not responses:

            return render_template("pagelast.html")

    return render_template("pagetwo.html", responses=responses)



@app.route("/pagelast", methods=["GET", "POST"])
def pagelast():
    """registration part 2 - user profile"""

    # TODO: render appropriate page to continue registration when needed

    responses = []

    if request.method == "GET":
        return render_template("pagelast.html")

    else:
        user = session["user_id"]

        # verify if pageTwo is complete
        check_p_two = db.execute("SELECT * FROM profiles WHERE user_ID = :user", user=user)

        if check_p_two == None:
            responses.append('Please complete your profile to register.')

        # append answers to table & direct user to generate.html
        else:
            answerA = request.form.get("answerA")
            answerB = request.form.get("answerB")

            db.execute("CREATE TABLE IF NOT EXISTS answers (user_id INT, answerA TEXT, answerB TEXT, FOREIGN KEY (user_id) REFERENCES users (userID))")
            db.execute("INSERT INTO answers (user_id, answerA, answerB) VALUES (:user, :answerA, :answerB)", user=user, answerA=answerA, answerB=answerB)
            db.execute("UPDATE users SET registered = 'Y' WHERE userID = :user", user=user)

            return render_template("generate.html", responses=responses)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
