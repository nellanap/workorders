import os

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from sqlalchemy import func
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from flask_session import Session


# Configure application
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
moment = Moment(app)




class Workorder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    apartment = db.Column(db.Text, nullable=True)
    type = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    closed = db.Column(db.Integer, nullable=True)
    updates = db.relationship('Update', backref='workorder', lazy='selectin')

    def __init__(self, apartment, type, description, closed):
        self.apartment = apartment
        self.type = type
        self.description = description
        self.closed = closed

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    workorder_id = db.Column(db.Integer, db.ForeignKey('workorder.id'))


    def __init__(self, status, workorder_id):
        self.status = status
        self.workorder_id = workorder_id


# Creates a new database but "heroku pg:reset DATABASE" first
db.create_all()
db.session.commit()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Show open workorders"""
    #open_workorders = Workorder.query.filter_by(closed=0)
    #open_workorders = (db.session.query(Workorder,Update).filter(Workorder.id == Update.workorder_id).filter_by(closed=0))
    #open_workorders = db.session.query(Workorder, Update).join(Update)

    #open_workorders = Workorder.query.join(Update, Workorder.id==Update.workorder_id).\
    #    add_columns(Workorder.apartment, Workorder.type, Workorder.description, Update.status).\
    #    filter(Workorder.closed==0)

    open_workorders = db.session.query(Workorder).\
        join(Update, Workorder.id==Update.workorder_id).\
        add_columns(Workorder.apartment, Workorder.type, Workorder.description, Update.status, Update.timestamp).\
        filter(Workorder.closed==0)

    return render_template("index.html", open_workorders=open_workorders)


@app.route("/add", methods=["GET", "POST"])
def add():
    """Add workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Add new workorder
        apartment=request.form.get("apartment")
        type=request.form.get("type")
        description=request.form.get("description")
        closed = 0
        new_workorder = Workorder(apartment, type, description, closed)
        db.session.add(new_workorder)
        db.session.commit()

        # Add new update
        new_update = Update("Task Created", new_workorder.id)
        db.session.add(new_update)
        db.session.commit()

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")

@app.route("/close", methods=["GET", "POST"])
def close():
    """Close workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Change workorder to closed
        workorder_id = request.form.get("workorder_id")
        closed_workorder = Workorder.query.get(workorder_id)
        closed_workorder.closed = 1
        db.session.commit()

        # Add final update
        status = request.form.get("status")
        new_update = Update(status, workorder_id)
        db.session.add(new_update)
        db.session.commit()

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        open_workorders = Workorder.query.filter_by(closed=0)
        return render_template("close.html", open_workorders=open_workorders)

@app.route("/history")
def history():
    """Show open workorders"""
    #open_workorders = Workorder.query.filter_by(closed=0)
    updates = Update.query.all()

    return render_template("history.html", updates=updates)


@app.route("/update", methods=["GET", "POST"])
def update():
    """Add an update to a workorder"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Add new status
        workorder_id = request.form.get("workorder_id")
        status = request.form.get("status")
        new_update = Update(status, workorder_id)
        db.session.add(new_update)
        db.session.commit()

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        open_workorders = Workorder.query.filter_by(closed=0)
        return render_template("update.html", open_workorders=open_workorders)
