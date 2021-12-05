
import os
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd
#DANDANDANDANDANDAQNDANDANDANDANDADNANDFNDSAFDA
#TESTING
#fjdklsafjdklsajfdsa
#fdjsakljfdsaklfdjsal
#ffdasjkl
#Cfdsakjlfdsajfdsa
#test
#MORE CHANGES

#BING BONG


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Show portfolio of stocks"""
    user = db.execute("SELECT * FROM users where id = :userid", userid=session["user_id"])
    balance = usd(user[0]["cash"])
    userstocks = db.execute(
        "SELECT symbol, SUM(shares) as shares FROM stocks WHERE user_id=:userid GROUP BY symbol HAVING SUM(shares) > 0", userid=session["user_id"])
   
    print(userstocks)
    for stock in userstocks:
        symbol = stock["symbol"]
        shares = stock["shares"]
        info = lookup(stock["symbol"])
        price = info["price"]
        name = info["name"]
        stock.update({"price":usd(price)})
        stock.update({"name":name})
        stock.update({"total":usd(price*shares)})
    # check = db.execute("SELECT SUM(shares) as shares FROM stocks WHERE user_id=:userid AND symbol =:symbol GROUP BY symbol HAVING SUM(shares) > 0", userid=session["user_id"], symbol = symbol['symbol'])
    
    return render_template('index.html',balance = balance, userstocks = userstocks)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    if request.method == "POST":
        # Ensuring that the user inputted a symbol & share(s)
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology ("Please provide share number(s) and a symbol", 400)
        symbol = lookup(request.form.get("symbol"))
        if not symbol:
            return apology("Symbol does not exist",400)
        shareprice = symbol["price"]
        # Creating a variable of the cash that the logged in user has
        usercash = db.execute("SELECT cash FROM users WHERE id = :userid", userid = session["user_id"])
        print(usercash)
        print(symbol)
        print(shareprice)
        shares = request.form.get("shares")
        if not shares.isdigit():
            return apology("Invalid share number",400)
        # Calculating the cost of the purchase
        finalcost = shareprice * int(request.form.get("shares"))
        # The amount of cash the user has left after the purchase
        updatedcost = float(usercash[0]['cash']) - finalcost
        print(updatedcost)
        # This ensures that the user has enough balance to complete the purchase
        if float(usercash[0]['cash']) < shareprice * int(request.form.get("shares")):
            return apology ("You do not have enough money to purchase", 400)
        # Update the users balance
        db.execute("UPDATE users SET cash = :updatedcost WHERE id = :userid", updatedcost = updatedcost, userid = session["user_id"])
        checkstock = db.execute("SELECT shares FROM stocks WHERE symbol =:symbolcheck", symbolcheck = request.form.get("symbol"))
        stockref= int(request.form.get("shares"))
        print(checkstock)
        # Checking to see whether the user has previously purchased the stock or not and if they have not, then putting that new stock into their account 
        date = datetime.now()
        time = date.time()
        print(date)
        if len(checkstock) == 1:
            finalcheck = checkstock[0]["shares"] + stockref
            
            #db.execute("UPDATE stocks SET shares = :finalcheck WHERE symbol = :symbol", finalcheck = finalcheck, symbol = request.form.get("symbol"))
            db.execute("INSERT INTO stocks(user_id,symbol,shares,price,date,time,operation) VALUES(:user_id,:symbol,:shares,:price,:date,:time,:operation)", user_id = session["user_id"], symbol = symbol['symbol'], shares = int(request.form.get("shares")), price = shareprice, date = date.strftime("%x"), time = time, operation= "BUY")
        else: 
            db.execute("INSERT INTO stocks(user_id,symbol,shares,price,date,time,operation) VALUES(:user_id,:symbol,:shares,:price,:date,:time,:operation)", user_id = session["user_id"], symbol = symbol['symbol'], shares = int(request.form.get("shares")), price = shareprice, date = date.strftime("%x"), time = time, operation = "BUY")
        return redirect("/")


@app.route("/history")
@login_required
def history():
    history = db.execute("SELECT * FROM stocks WHERE user_id =:userid", userid = session["user_id"])
    print(history)
    return render_template("history.html", history = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        rows = lookup(request.form.get("symbol"))
        # Check to see if the symbol exists 
        if not rows:
            return apology ("This symbol does not exist in our database",400)
        return render_template("quoted.html", stock = rows)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure that the username was submitted 
        if not request.form.get("username"):
            return apology ("Username must be provided", 400)
        # Ensure that the password was submitted
        elif not request.form.get("password"):
            return apology ("Password must be provided", 400)
        elif (len(request.form.get("password")) < 7):
            return apology("Password must be at least 7 characters!", 400)
        # Ensure that the password confirmation was entered
        elif not request.form.get("confirmation"):
            return apology ("Must confirm password", 400)
        # Make sure that the passwords match 
        elif (request.form.get("password") != request.form.get("confirmation")):
            return apology ("Passwords do not match", 400)
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        # Checking the availablity of the username 
        if (len(rows) != 0):
            return apology ("Username already taken", 400)
        # If the username is not taken, transfer the inputted information to the database and replace the password for a hash 
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username = request.form.get("username"), password = generate_password_hash(request.form.get("password")))
        return apology ("You are registered", 200)
    else: 
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    history = db.execute("SELECT symbol FROM stocks WHERE user_id =:userid GROUP BY symbol", userid = session["user_id"])
    if request.method == "GET":
        
        return render_template("sell.html", HISTORY = history)
    if request.method == "POST":
        val = str(request.form.get("symbol"))
        symbol = lookup(val)
        if not symbol:
            return apology("Symbol does not exist")
        soldshares = request.form.get("shares")
        if not soldshares:
            return apology("Please enter a number of shares")
        finalshares = int(soldshares)
        ownedshares = db.execute("SELECT SUM(shares) as shares FROM stocks WHERE user_id=:userid AND symbol = :symbol GROUP BY symbol", userid=session["user_id"], symbol = symbol['symbol'])
        print(ownedshares)
        if not ownedshares or ownedshares[0]["shares"]<finalshares:
            return apology("You do not have enough shares to sell")
        else:    
            sharecost = finalshares * symbol["price"]
            total = db.execute("SELECT cash FROM users where id=:id", id = session["user_id"])
            finaltotal = sharecost + total[0]["cash"]
            db.execute("UPDATE users SET cash =:finaltotal WHERE id =:id", id = session["user_id"], finaltotal = finaltotal)
            newshares = ownedshares[0]["shares"]
            if newshares < 0:
                db.execute("DELETE FROM stocks WHERE user_id=:user_id AND symbol =:symbol", user_id = session["user_id"], symbol=symbol["symbol"])
            #else:
                #db.execute("UPDATE stocks SET shares=:shares WHERE user_id=:user_id AND symbol=:symbol", shares=newshares, user_id=session["user_id"], symbol = symbol["symbol"])
            shareprice = symbol["price"]
            date = datetime.now()
            time = date.time()
            db.execute("INSERT INTO stocks(user_id,symbol,shares,price,date,time,operation) VALUES(:user_id,:symbol,:shares,:price,:date,:time,:operation)", user_id = session["user_id"], symbol = symbol['symbol'], shares = -(int(request.form.get("shares"))), price = shareprice, date = date.strftime("%x"), time = time, operation = "SELL")
            
            return redirect("/")
            

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
