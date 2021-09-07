import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime

from helpers import login_required, lookup, usd, news_lookup

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
db = SQL("sqlite:///crypto.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    grand_total = 0;
    
    rows = db.execute("SELECT ticker_symbol, shares, cash FROM portfolio JOIN users ON portfolio.user_id = users.id WHERE user_id = ?", session["user_id"])
    
    if not rows:
        user_cash = (db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"]))[0]["cash"]
        grand_total = user_cash
        flash('Portfolio currently empty.')
        return render_template("index.html", user_cash=user_cash, grand_total=grand_total)
    else:
        user_cash = rows[0]["cash"]
        
        for row in rows:
            row["Current_Stock_Price"] = (lookup(row["ticker_symbol"]))["price"]
            row["Current_total_holding_value"] = row["Current_Stock_Price"] * row["shares"]
            grand_total += row["Current_total_holding_value"] 
        
        grand_total += user_cash
        
        
        
        return render_template("index.html", rows=rows, user_cash=user_cash, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        
        shares = request.form.get("shares") # "shares" is the amount of money the user wants to put into a certain crypto.
        ticker_symb = lookup((request.form.get("symbol")).upper())
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        if not request.form.get("symbol"):
            return render_template("buy.html", user_cash=user_cash[0]["cash"], error_message_buy="Please enter a cryptocurrency ticker.")
        if ticker_symb == None:
            return render_template("buy.html", user_cash=user_cash[0]["cash"], error_message_buy="Sorry, could not find that cryptocurrency.")
        if not request.form.get("shares"):
            return render_template("buy.html", user_cash=user_cash[0]["cash"], error_message_buy="Please enter the amount you would like to buy.")
        if float(shares) <= 0:
            return render_template("buy.html", user_cash=user_cash[0]["cash"], error_message_buy="Invalid amount.")

        shares = float(shares)
        if user_cash[0]["cash"] < shares: #try changing this so that users can say how much money they want to spend on a crypto instead of how many shares they want to buy, making partial shares possible.
            return render_template("buy.html", user_cash=user_cash[0]["cash"], error_message_buy="Insufficient funds.")
        
        user_cash[0]["cash"] -= shares
        db.execute("INSERT INTO transactions (user_id, ticker_symbol, shares, share_price, total_value, date_, time_, transaction_type) VALUES(?, ?, ?, ?, ?, date('now'), time('now'), 'BUY')", session["user_id"], ticker_symb["symbol"], (shares/ticker_symb["price"]), ticker_symb["price"], shares)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash[0]["cash"], session["user_id"])
        
        user_shares = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND ticker_symbol = ?", session["user_id"], ticker_symb["symbol"])
        
        if not user_shares:
            db.execute("INSERT INTO portfolio (user_id, ticker_symbol, shares) VALUES(?, ?, ?)", session["user_id"], ticker_symb["symbol"], (shares/ticker_symb["price"]))
        elif user_shares[0]["shares"] > 0:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND ticker_symbol = ?", (user_shares[0]["shares"] + (shares/ticker_symb["price"])), session["user_id"], ticker_symb["symbol"])
        
        flash('Successfully Bought.')
        return redirect("/")
    else:
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        if user_cash[0]["cash"] == 0:
            return render_template("buy.html", message="Account cash balance empty.")
        return render_template("buy.html", user_cash=user_cash[0]["cash"])


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""
    if request.method == "POST":
        if not request.form.get("date"):
            flash('Please select a timeline.')
            return redirect("/history")
        
        history = db.execute("SELECT ticker_symbol, shares, share_price, total_value, date_, time_, transaction_type FROM transactions WHERE user_id = ? AND date_ BETWEEN date('now', ?) AND date('now') ORDER BY(transaction_id) DESC", session["user_id"], request.form.get("date"))
    
        if not history:
            return render_template("history.html", message="No transaction history to show.")
        
        return render_template("history.html", history=history)

    else:
        return render_template("history.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error_message_login="Please enter username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error_message_login="Please enter password.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error_message_login="Invalid username and/or password.")

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

        ticker_symb = lookup((request.form.get("symbol")).upper())
        if not request.form.get("symbol"):
            flash('Please enter a cryptocurrency ticker.')
            return redirect("/quote")
        elif ticker_symb == None:
            flash('Sorry, we could not find that cryptocurrency.')
            return redirect("/quote")
        return render_template("quoted.html", ticker_symb=ticker_symb)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            flash('Please provide a username.')
            return redirect("/register")
        elif not password or not confirmation:
            flash('Please provide a password.')
            return redirect("/register")
        elif len(password) < 5:
            flash('Password must be atleast 5 characters long.')
            return redirect("/register")
        elif password != confirmation:
            flash('Passwords do not match.')
            return redirect("/register")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) == 1:
            flash('Username is already taken.')
            return redirect("/register")

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))
        return render_template("login.html", message="Registration complete.")

    else:
        return render_template("register.html")
        

@app.route("/reset", methods=["GET", "POST"])
@login_required
def reset():
    """Reset user password"""
    if request.method == "POST":

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not password or not confirmation:
            flash('Please enter password.')
            return redirect("/reset")
        elif len(password) < 5:
            flash('Password must be atleast 5 characters long.')
            return redirect("/reset")
        elif password != confirmation:
            flash('Passwords do not match')
            return redirect("/reset")

        user_hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

        if check_password_hash(user_hash[0]["hash"], password):
            flash('New password cannot be the same as the current password.')
            return redirect("/reset")

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(password), session["user_id"])

        flash('Password Successfully Changed.')
        return redirect("/")
        
    else:
        return render_template("Reset_Password.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    
    if request.method == "POST":
        
        user_stocks = db.execute("SELECT ticker_symbol, shares FROM portfolio WHERE user_id = ?", session["user_id"])
        
        if not request.form.get("symbol"):
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Please select a cryptocurrency to sell.")
        if not request.form.get("shares"):
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Please enter the amount to sell.")
            
        ticker_symb = lookup(request.form.get("symbol"))
        shares = request.form.get("shares")
        user_shares = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND ticker_symbol = ?", session["user_id"], ticker_symb["symbol"])
        
        if not user_shares:
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Sorry, you do not own any of that cryptocurrency.")
        
        if not request.form.get("symbol"):
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Please select a cryptocurrency to sell.")
        elif float(shares) <= 0:
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Please enter a positive number of shares to sell.")
        elif user_shares[0]["shares"] < float(shares):
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="Sorry, please enter an amount within your current holding.")
            
        shares = float(shares)    
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        user_shares[0]["shares"] -= shares
        user_cash[0]["cash"] += (shares * ticker_symb["price"])
        
        db.execute("INSERT INTO transactions (user_id, ticker_symbol, shares, share_price, total_value, date_, time_ , transaction_type) VALUES(?, ?, ?, ?, ?, date('now'), time('now'), 'SELL')", session["user_id"], ticker_symb["symbol"], shares, ticker_symb["price"], shares*ticker_symb["price"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash[0]["cash"], session["user_id"])
        
        if user_shares[0]["shares"] > 0:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND ticker_symbol = ?", user_shares[0]["shares"], session["user_id"], ticker_symb["symbol"])
        else:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND ticker_symbol = ?", session["user_id"], ticker_symb["symbol"])
            
        flash('Successfully Sold.')
        return redirect("/")

    else:

        user_stocks = db.execute("SELECT ticker_symbol, shares FROM portfolio WHERE user_id = ?", session["user_id"])
        if not user_stocks:
            return render_template("sell.html", user_stocks=user_stocks, error_message_sell="No cryptocurrency currently owned.")
        return render_template("sell.html", user_stocks=user_stocks)
        
        
@app.route("/news", methods=["GET", "POST"])
@login_required
def news():
    """News on certain cryptos"""
    if request.method == "POST":
        
        ticker_symb = lookup((request.form.get("symbol")).upper())
        ticker_news = news_lookup((request.form.get("symbol")).upper())
        if not request.form.get("symbol"):
            return render_template("news.html", message="Please enter a crypto to lookup.")
        elif not ticker_news or not ticker_symb:
            return render_template("news.html", message="Sorry, could not find that cryptocurrency.")
        
            
        return render_template("news.html", ticker_news=ticker_news, ticker_symb=ticker_symb)
        
    else:
        return render_template("news.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)