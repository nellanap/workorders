import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup

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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///workorder.db")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    open_workorders = db.execute("SELECT apartment, type, description, status, timestamp FROM workorders INNER JOIN updates ON workorders.id = updates.workorder_id WHERE closed = 0 GROUP BY workorders.id")

    return render_template("index.html", open_workorders=open_workorders)


@app.route("/add", methods=["GET", "POST"])
def add():
    """Add work order"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        apartment=request.form.get("apartment")
        type=request.form.get("type")
        description=request.form.get("description")
        closed = 0

        # Add to workorders table
        db.execute("INSERT INTO 'workorders' (user_id, apartment, type, description, closed) VALUES (:user_id, :apartment, :type, :description, :closed)", user_id=session["user_id"], apartment=apartment, type=type, description=description, closed=closed)

        # Select the workorder_id from the newly added workorder
        rows = db.execute("SELECT id FROM workorders WHERE apartment = apartment AND type = type AND description = description ORDER BY id DESC")
        workorder_id = rows[0]["id"]
        status = "no status yet"

        # Add a straw status update to updates
        db.execute("INSERT INTO 'updates' (workorder_id, status) VALUES(:workorder_id, :status)", workorder_id=workorder_id, status=status)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    updates = db.execute("SELECT apartment, type, description, status, timestamp FROM workorders INNER JOIN updates ON workorders.id = updates.workorder_id ORDER BY timestamp DESC")

    return render_template("history.html", updates=updates)

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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation")

        # Ensure password and confirmation are the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must provide same password and confirmation")

        # Generate password hash
        hash = generate_password_hash(request.form.get("password"))

        # Add user to database
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hash)

        if not result:
            return apology("must provide unique username")

        # login the user
        session["user_id"] = result

        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Add an update to a workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        db.execute("INSERT INTO 'updates' (workorder_id, status) VALUES(:workorder_id, :status)", workorder_id=request.form.get("workorder_id"), status=request.form.get("status"))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        open_workorders = db.execute("SELECT id, user_id, apartment, type, description FROM workorders WHERE closed = 0")
        return render_template("update.html", open_workorders=open_workorders)


@app.route("/close", methods=["GET", "POST"])
@login_required
def close():
    """Add an update to a workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        closed = request.form.get("closed")
        workorder_id = request.form.get("workorder_id")
        status = request.form.get("status")

        db.execute("INSERT INTO updates (workorder_id, status) VALUES(:workorder_id, :status)", workorder_id=workorder_id, status=status)

        db.execute("UPDATE workorders SET closed = :closed WHERE id = :workorder_id", closed=closed, workorder_id=workorder_id)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        open_workorders = db.execute("SELECT id, user_id, apartment, type, description FROM workorders WHERE closed = 0")
        return render_template("close.html", open_workorders=open_workorders)

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
