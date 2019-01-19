import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from flask_session import Session


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


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///workorder.db")

@app.route("/")
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
        db.execute("INSERT INTO 'workorders' (apartment, type, description, closed) VALUES (:apartment, :type, :description, :closed)", apartment=apartment, type=type, description=description, closed=closed)

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
def history():
    """Show history of transactions"""
    updates = db.execute("SELECT apartment, type, description, status, timestamp FROM workorders INNER JOIN updates ON workorders.id = updates.workorder_id ORDER BY timestamp DESC")

    return render_template("history.html", updates=updates)


@app.route("/update", methods=["GET", "POST"])
def update():
    """Add an update to a workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        db.execute("INSERT INTO 'updates' (workorder_id, status) VALUES(:workorder_id, :status)", workorder_id=request.form.get("workorder_id"), status=request.form.get("status"))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        open_workorders = db.execute("SELECT id, apartment, type, description FROM workorders WHERE closed = 0")
        return render_template("update.html", open_workorders=open_workorders)


@app.route("/close", methods=["GET", "POST"])
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
        open_workorders = db.execute("SELECT id, apartment, type, description FROM workorders WHERE closed = 0")
        return render_template("close.html", open_workorders=open_workorders)


