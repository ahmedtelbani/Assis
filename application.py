import os
import urllib, json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
import time
import re

from helpers import apology, login_required, lookup, usd

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
db = SQL("sqlite:///assis.db")


yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
today = datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')


def convert(days_list):
    newList = []

    for day in days_list:
        if day == today:
            newList.append("Today")
        elif day == yesterday:
            newList.append("Yesterday")
        elif day == tomorrow:
            newList.append("Tomorrow")
        else:
            newList.append(day)
    return newList



@app.route("/", methods=["GET"])
def home():
    """Show home page"""
    if request.method == "GET":
        return render_template("/home.html")



@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    """Show tasks page"""
    if request.method == "GET":
        user_id = session["user_id"]

        tasks = {}

        # get days from db
        dates = db.execute("SELECT DISTINCT date FROM tasks WHERE user_id=:p_id ORDER BY date DESC", p_id=user_id)

        # add each date in a list
        task_dates = [ date['date'] for date in dates ]

        # get every task in each spasific day from db in a dict
        for date in task_dates:
            task_row = db.execute("SELECT id, task, checked FROM tasks WHERE user_id=:p_id AND date=:p_date", p_id=user_id, p_date=date)
            tasks[date] = task_row

        days = list(tasks.keys())
        day_lenth = len(days)

        display = "none"

        if day_lenth == 0:
            display = "block"

        # convert dates to (today or yesterday or tomorrow or date)
        newDays = convert(days)

        # send data
        return render_template("/tasks.html", day_lenth=day_lenth, tasks=tasks, days=days, newDays=newDays, display=display)

    # if request Method = POST
    elif request.method == "POST":
        button_name = request.form.get("task_btn")
        if button_name == "delete":
            task_id = request.form.get("task_id")
            db.execute("DELETE FROM tasks WHERE id=:p_id;", p_id=task_id)
        elif button_name == "add":
            user_id = session["user_id"]
            task = request.form.get("task")
            date = request.form.get("date")
            checked = 0

            if task == "":
                flash("You didn't type the name of task !! \t try again, Please")
            else:
                # add task to database
                result = db.execute("INSERT INTO tasks (user_id, task, checked, date) VALUES (:p_id, :p_task, :p_checked, :p_date)", p_id=user_id, p_task=task, p_checked=checked, p_date=date)


            return redirect("/tasks")

        elif button_name == "edit_show":
            task_id = request.form.get("task_id")
            task_info = db.execute("SELECT id, task, date FROM tasks WHERE id=:p_id", p_id=task_id)

            task_id = task_info[0]["id"]
            name = task_info[0]["task"]
            date = task_info[0]["date"]

            visibility = "visible"
            opacity = "1"

            return redirect(url_for('tasks', visibility=visibility, opacity=opacity, task_id=task_id, name=name, date=date, **request.args))

        elif button_name == "edit":
            task_id = request.form.get("task_id")
            name = request.form.get("task")
            date = request.form.get("date")

            result = db.execute("UPDATE tasks SET task=:p_name, date=:p_date WHERE id=:p_id", p_name=name, p_date=date, p_id=task_id)

            return redirect("/tasks")

        else:
            task_id = request.form.get("task_id")

            task_checked = db.execute("SELECT checked FROM tasks WHERE id=:p_id", p_id=task_id)[0]["Checked"]

            if task_checked == 0:
                result = db.execute("UPDATE tasks SET checked=:p_check WHERE id=:p_id", p_check=1, p_id=task_id)
            elif task_checked == 1:
                result = db.execute("UPDATE tasks SET checked=:p_check WHERE id=:p_id", p_check=0, p_id=task_id)
            return redirect("/tasks")



        return redirect("/tasks")





@app.route("/random", methods=["GET", "POST"])
@login_required
def random():
    """Show random page"""
    if request.method == "GET":
        visibility = "hidden"
        return render_template("/random.html", visibility=visibility)

    elif request.method == "POST":
        activity = "Play"
        api_url = "https://www.boredapi.com/api/activity"

        with urllib.request.urlopen(api_url) as url:
            data = json.loads(url.read().decode())
            print(data)

        activity = data["activity"]
        r_type = data["type"]
        participants = data["participants"]
        price = data["price"]
        link = data["link"]
        accessibility = data["accessibility"]

        visibility = "visible"

        if link == "":
            link = "Just do it"

        return render_template("/random.html", activity=activity, r_type=r_type, participants=participants, price=price, link=link, accessibility=accessibility, visibility=visibility)



@app.route("/pomodoro", methods=["GET", "POST"])
@login_required
def pomodoro():
    """Show pomodoro page"""
    if request.method == "GET":
        user_id = session["user_id"]

        pomo_data = db.execute("SELECT pomo_number, breaks_number, pomo_time, breaks_time FROM users WHERE id=:p_id", p_id=user_id)
        pomo_number = pomo_data[0]["pomo_number"]
        breaks_number = pomo_data[0]["breaks_number"]
        pomo_time = pomo_data[0]["pomo_time"]
        breaks_time = pomo_data[0]["breaks_time"]

        return render_template("/pomodoro.html", pomo_number=pomo_number, breaks_number=breaks_number, pomo_time=pomo_time, breaks_time=breaks_time)

    elif request.method == "POST":
        user_id = session["user_id"]
        button_name = request.form.get("pomo_act")

        print(button_name)
        pomo_data = db.execute("SELECT pomo_number, breaks_number, pomo_time, breaks_time FROM users WHERE id=:p_id", p_id=user_id)

        if button_name == "pomo":

            pomo_number = (pomo_data[0]["pomo_number"]) + 1
            breaks_number = (pomo_data[0]["breaks_number"])
            pomo_time = (pomo_data[0]["pomo_time"]) + 25
            breaks_time = (pomo_data[0]["breaks_time"])

            result = db.execute("UPDATE users SET pomo_number=:p_number, breaks_number=:p_tn, pomo_time=:p_tim, breaks_time=:p_tt WHERE id=:p_id", p_number=pomo_number, p_tn=breaks_number, p_tim=pomo_time, p_tt=breaks_time, p_id=user_id)
            return redirect("/pomodoro")

        elif button_name == "rest":

            pomo_number = (pomo_data[0]["pomo_number"])
            breaks_number = (pomo_data[0]["breaks_number"]) + 1
            pomo_time = (pomo_data[0]["pomo_time"])
            breaks_time = (pomo_data[0]["breaks_time"]) + 5

            result = db.execute("UPDATE users SET pomo_number=:p_number, breaks_number=:p_tn, pomo_time=:p_tim, breaks_time=:p_tt WHERE id=:p_id", p_number=pomo_number, p_tn=breaks_number, p_tim=pomo_time, p_tt=breaks_time, p_id=user_id)
            return redirect("/pomodoro")



@app.route("/timer", methods=["GET", "POST"])
@login_required
def timer():
    """Show timer page"""
    if request.method == "GET":
        function = ""
        function = request.args.get("function")
        return render_template("/timer.html", function=function)




@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    """Show notes page"""
    if request.method == "GET":

        user_id = session["user_id"]

        labels_query = db.execute("SELECT DISTINCT label FROM notes WHERE user_id=:p_id", p_id=user_id)
        labels = [label['label'] for label in labels_query]

        for label in labels:
            if label == "":
                labels.remove("")
                labels.insert(0,"New")

        notes = db.execute("SELECT id, label, title, content FROM notes WHERE user_id=:p_id ORDER BY id DESC", p_id=user_id)

        return render_template("/notes.html", labels=labels, notes=notes)


    elif request.method == "POST":

        button_name = request.form.get("notes_btn")
        user_id = session["user_id"]
        print(button_name)


        if button_name == "add":
            sql = "INSERT INTO notes (user_id, label, title, content) VALUES (:user_id, :label, :title, :content)"
            result = db.execute(sql, user_id=user_id, label="", title="", content="")

        elif button_name == "delete":
            note_id = request.form.get("note_id")
            db.execute("DELETE FROM notes WHERE id=:p_id", p_id=note_id)

        elif button_name == "save":
            note_id = request.form.get("note_id")
            note_label = ""
            note_title = ""
            note_content = ""

            result = db.execute("UPDATE notes SET label=:p_label, title=:p_title, content=:p_content WHERE id=:p_id", p_label=note_label, p_title=note_title, p_content=note_content, p_id=note_id)

            print("save")

        return redirect("/notes")


@app.route("/profile", methods=["GET"])
def profile():
    """Show profile page"""
    if request.method == "GET":
        return render_template("/profile.html")

@app.route("/about", methods=["GET"])
def about():
    """Show about page"""
    if request.method == "GET":
        return render_template("/about.html")



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
        return redirect("/tasks")

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
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure passwords is match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("Password does not match", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        hash_password = generate_password_hash(password)

        # Ensure username is not exist
        name = db.execute('SELECT username FROM users WHERE username = :uname', uname=username)
        if name:
            if name[0]['username'] == username:
                return apology("The username is already taken", 400)

        # Insert user into database
        sql = "INSERT INTO users (username, hash) VALUES (:username, :hashed)"
        result = db.execute(sql, username=username, hashed=hash_password)

        # remember user
        session["user_id"] = result

        # redirect user to home page
        return redirect("/tasks")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
