import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from time import sleep

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user = session["user_id"]

    # find current cash balance after buy/sell
    q = db.execute("SELECT SUM(cash) FROM users WHERE id = :user", user=user)
    cash_balance = float(q[0]['SUM(cash)'])

    # define variables
    ttl_balance = 0
    paid = 0
    valued = 0

    # create a new table "shares" if not there & search user holding data - store in "holdings"
    db.execute("CREATE TABLE IF NOT EXISTS shares (actionType VARCHAR(255), user_ID INT, symbol VARCHAR(255), name VARCHAR(255), s_count INT, unit FLOAT, priced FLOAT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id))")
    holdings = db.execute("SELECT SUM(priced) AS TotalPaid, symbol, SUM(s_count) AS TotalCount FROM shares WHERE user_ID = :user AND actionType = 'BUY' OR actionType = 'SELL' GROUP BY symbol", user=user)

    # remove previous userID index
    db.execute("DROP INDEX IF EXISTS userid")

    # create new userID index
    db.execute("CREATE INDEX IF NOT EXISTS userid ON shares (user_ID)")

    if holdings == None:
        return render_template("index.html", cash_balance=usd(cash_balance))

    else:

        for row in range(len(holdings)):

            # look up symbol in API
            symbol = holdings[row]['symbol']
            looked = lookup(symbol)
            name = looked['name']

            # find unit price for each stock
            price = float(looked['price'])

            # find total shares for each stock
            TotalCount = int(holdings[row]['TotalCount'])

            if TotalCount <= 0:
                continue

            else:
                # subttl(total value of each share type) & valued(SUM of all subttl)
                subttl = float("{:.2f}".format(price * TotalCount))
                valued += subttl

                # add all previously paid prices to find cash balance
                paid = paid + float(holdings[row]['TotalPaid'])

                db.execute("INSERT INTO shares (actionType, symbol, name, unit, s_count, priced) VALUES ('indexed', :symbol, :name, :unit, :s_count, :priced)", symbol=symbol, name=name, unit=price, s_count=TotalCount, priced=usd(subttl))

        stocks = db.execute("SELECT symbol, name, unit, s_count, priced FROM shares WHERE actionType = 'indexed'")
        cash_balance = cash_balance - paid
        ttl_balance = cash_balance + valued
        db.execute("DELETE FROM shares WHERE actionType = 'indexed'")

        return render_template("index.html", stocks=stocks, cash_balance=usd(cash_balance), ttl_balance=usd(ttl_balance))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    responses = []

    user = session["user_id"]
    # User reached route via POST (as by submitting a form via POST)

    if request.method == "GET":
        return render_template("buy.html")

    else:

        # look up API for the symbol input to get quoted
        quoted = lookup(request.form.get("co_code"))

        if not quoted:
            responses.append('Not a valid symbol')

        else:

            # store share count to purchase & find the unit price
            count = int(request.form.get("n_shares"))
            unit = float(quoted["price"])

            # store total price, name of the company, and symbol
            priced = float("{:.2f}".format(unit * count))

            # check available cash from user account
            query = db.execute("SELECT cash FROM users WHERE id = :user", user=user)
            cash = float(query[0]['cash'])

            # get total changes from previous buy/sell and calculate cash balance
            query = db.execute("SELECT SUM(priced) as totalPriced FROM shares WHERE user_ID = :user;", user=user)

            if query[0]['totalPriced'] == None:
                changes = 0

            else:
                changes = float(query[0]['totalPriced'])

            balance = cash - changes
            name = str(quoted["name"])
            symbol = str(quoted["symbol"])

            # if not enough cash, apology
            # TODO: add options to get more cash?
            if priced > balance:
                responses.append('Not enough cash')

            if not responses:

                # add share data into shares & respond with summary display (bought.html)
                db.execute("INSERT INTO shares (actionType, user_ID, name, priced, symbol, s_count, unit) VALUES ('BUY', :user, :name, :priced, :symbol, :count, :unit)", user=user, name=name, priced=priced, symbol=symbol, count=count, unit=unit)
                balance = balance - priced

                return render_template("bought.html", name=name, symbol=symbol, count=count, quoted=unit, valued=usd(priced), balance=usd(balance))
                sleep(1.8)

                return redirect("/")

        # Redirect user to home page
        return render_template("buy.html", responses=responses)



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user = session["user_id"]
    records = db.execute("SELECT TIMESTAMP, name, symbol, actionType, s_count, priced FROM shares WHERE user_ID = :user ORDER BY TIMESTAMP DESC", user=user)

    if records == None:
        return render_template("history.html", message="No transaction history (yet)")

    else:
        return render_template("history.html", records=records)



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

            print(responses)

        if not responses:

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")

        else:
            return render_template("login.html", responses=responses)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    responses = []
    if request.method == "GET":
        return render_template("quote.html")

    else:

        # fetch data for the co_code(stock symbol) and error if input is missing
        # TODO: deactivate the button if co_code is missing
        find = request.form.get("quote_this")

        if not find:

            # display some sort of error until corrected
            responses.append('Could not find the symbol')

        else:

            # store lookup result in "quoted"
            # TODO: if no data is found display message on the same page

            quoted = lookup(request.form.get("quote_this"))
            quote = float("{:.2f}".format(quoted['price']))
            time = datetime.datetime.now()
            if quoted == None:
                responses.append('No data available')

            # when successful direct to quoted.html and display results
            else:
                return render_template("quoted.html", time=time, name=quoted['name'], symbol=quoted['symbol'], price=usd(quote))

    return 0


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    responses = []
    if request.method == "GET":
        return render_template("register.html", responses=responses)

    else:
        # if user submits input, verify name is provided and it's unique
        found_name = db.execute("SELECT * FROM users WHERE username = :newname", newname=request.form.get("newname"))
        print(found_name)

        if len(found_name) != 0:
            responses.append('That username is taken - please pick another')

        else:
            # verify password is provided and it matches with "confirm"
            if request.form.get("password") != request.form.get("confirm"):
                responses.append('The passwords do not match')

            else:
                # hash the password to get pw_hash & add both username and pw_hash to table "users"
                newname=request.form.get("newname")
                pw_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
                db.execute("INSERT INTO users (username, hash) VALUES (:newname, :pw_hash)", newname=newname, pw_hash=pw_hash)

                rows = db.execute("SELECT * FROM users WHERE username = :newname", newname=newname)
                session["user_id"] = rows[0]["id"]

                if not responses:
                    # create a new table "actions" if not there & insert user_ID and actionType "registered"
                    db.execute("CREATE TABLE IF NOT EXISTS actions (user_ID INT, symbol VARCHAR(255), name VARCHAR(255), lastPrice FLOAT, actionType VARCHAR(255), Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id))")
                    db.execute("INSERT INTO actions (actionType, user_ID) VALUES ('registered', (SELECT id FROM users WHERE username = :newname))", newname=newname)

                    # get the username and display welcome message for .5 seconds
                    rows = db.execute("SELECT users.username, actions.actionType FROM users, actions WHERE users.username = :newname", newname=newname)

                    return render_template("registered.html", username=newname)
                    sleep(.5)

                    # Redirect user to home page
                    return redirect("/")

    return render_template("register.html", responses=responses)



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    holdings = []
    responses = []
    user = session["user_id"]
    # find the current holdings & if no holdings display message "no shares to sell" (redirect to /buy?)
    h = db.execute("SELECT SUM(priced) AS TotalPaid, symbol, SUM(s_count) AS TotalCount FROM shares WHERE user_ID = :user AND actionType = 'BUY' OR actionType = 'SELL' GROUP BY symbol", user=user)
    shares = (row for row in h if row['TotalCount'] > 0)
    holdings = [row['symbol'] for row in shares]

    # display sell.html & render dropdown menu with symbol data from 'holdings'
    if request.method == "GET":

        if h == None:
            responses.append('No shares to sell')

        else:
            return render_template("sell.html", holdings=holdings)

    else:

        symbol = request.form.get("symbol")
        nbr = int(request.form.get("units"))

        # ensure enough shares to sell
        units = db.execute("SELECT SUM(s_count) AS TotalCount FROM shares WHERE user_ID = :user AND symbol = :symbol GROUP BY symbol", user=user, symbol=symbol)
        units = int(units[0]['TotalCount'])

        if nbr > units:
            responses.append('Not enough shares in your holdings')

        else:

            # query API and calculate values
            looked = lookup(symbol)
            quoted = float(looked['price'])
            name = looked['name']
            valued = float("{:.2f}".format(quoted * nbr))
            valued = valued * -1

            nbr = nbr * -1

        if not responses:

            # add transaction to "shares"
            db.execute("INSERT INTO shares (actionType, user_ID, symbol, name, unit, s_count, priced) VALUES ('SELL', :user, :symbol, :name, :unit, :s_count, :priced)", user=user, symbol=symbol, name=name, unit=quoted, s_count=nbr, priced=valued)
            valued = valued * -1

            # display a message with sold share info
            return render_template("sold.html", name=name, symbol=symbol, quoted=quoted, valued=usd(valued))
            sleep(2.0)

            # Redirect user to home page
            return redirect("/")

    return render_template("sell.html", responses=responses, holdings=holdings)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
