import os
import re
import vonage
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_wtf import FlaskForm

from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup
from flask_mail import Mail, Message


from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

app.config["MAIL_DEFAULT_SENDER"] = "DEFAULT EMAIL RECIPIENT, WHEN UNSPECIFIED"
app.config["MAIL_USERNAME"] = "YOUR EMAIL ADDRESS"
app.config["MAIL_PASSWORD"] = "EMAIL PASSWORD"
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

db = SQL("sqlite:///weather.db")

vonage_key = ""
vonage_secret = ""

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

def sensor():
    ids_list = []
    due_ids = db.execute("SELECT * FROM reminders WHERE ((DATE() >= date AND TIME() >= time) OR (DATE() > date)) AND reminder_status = 1")
    for item in due_ids:
        form_id = item["id"]
        user_id = item["user_id"]
        reminder_type = item["type"]
        details = db.execute("SELECT * FROM users WHERE id = ?;", user_id)[0]
        if(reminder_type == "email"):
            email = details["username"]
            send_mail(email, form_id)
            db.execute("UPDATE reminders SET reminder_status = 0, sent_status = 1 WHERE id = ?", form_id)
            print("Sending email")
        if(reminder_type == "text"):
            phone_number = details["phone_number"]
            send_txt(phone_number, form_id)
            db.execute("UPDATE reminders SET reminder_status = 0, sent_status = 1 WHERE id = ?", form_id)
            print("Sending text")
    print("All messages sent")

sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor,'interval',minutes=1)
sched.start()


def send_mail(recipient, form_id):
    with app.app_context():
        reminders = db.execute("SELECT * FROM reminders WHERE id = ?;", form_id)[0]
        #title = reminders["cityname"] + " Weather " + reminders["date"]
        message = Message("Weather", recipients=[recipient])

        message.body = reminders["cityname"] + " Weather " + reminders["date"] + "\n\n"

        hourlist = []
        data = lookup(reminders["cityname"])
        for number in range(23):
            if data["forecast"]["hour"][number]["will_it_rain"] == 1:
                temp = { number : data["forecast"]["hour"][number]["chance_of_rain"] }
                hourlist.append(temp.copy())
        if(hourlist):
            message.body += "It could rain at:\n"
            for entry in hourlist:
                for key, value in entry.items():
                    message.body += str(key) + " "
                    message.body += str(value) + "%" + "\n"
        else:
            message.body += "There's no expected rain today.\n"
        mail.send(message)

def send_txt(phone_number, form_id):
    client = vonage.Client(key=vonage_key, secret=vonage_secret)
    sms = vonage.Sms(client)

    reminders = db.execute("SELECT * FROM reminders WHERE id = ?;", form_id)[0]
    string = reminders["cityname"] + " Weather " + reminders["date"]

    hourlist = []
    data = lookup(reminders["cityname"])
    for number in range(23):
        if data["forecast"]["hour"][number]["will_it_rain"] == 1:
            temp = { number : data["forecast"]["hour"][number]["chance_of_rain"] }
            hourlist.append(temp.copy())

    if(hourlist):
        string += "It could rain at:"
        for entry in hourlist:
            for key, value in entry.items():
                string += str(key) + "-"
                string += str(value) + "%" + ","
    else:
        string += "There's no expected rain today."
    responseData = sms.send_message(
    {
        "from": "Rain?",
        "to": phone_number,
        "text": string,
    }
    )
    if responseData["messages"][0]["status"] == "0":
        pass
    else:
        return apology("Message Failed", 202)

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        form_id = request.form.get("id")
        user_id = db.execute("SELECT user_id FROM reminders WHERE id = ?;", form_id)[0]["user_id"]
        reminder_type = db.execute("SELECT type FROM reminders WHERE id = ?;", form_id)[0]["type"]
        details = db.execute("SELECT * FROM users WHERE id = ?;", user_id)[0]
        if(reminder_type == "email"):
            email = details["username"]
            send_mail(email, form_id)

        elif(reminder_type == "text"):
            phone_number = details["phone_number"]
            send_txt(phone_number, form_id)
        return redirect("/history")
    else:
        user_id = session["user_id"]
        details = db.execute("SELECT * FROM users WHERE id = ?;", user_id)[0]
        reminders = db.execute("SELECT * FROM reminders WHERE user_id = ? ORDER BY datetime DESC;", user_id)
        if len(reminders) == 0:
            return apology("No Reminders set", 400)
        return render_template("history.html", reminders = reminders, details = details)


@app.route("/reminder", methods=["GET", "POST"])
@login_required
def reminder():
    user_id = session["user_id"]
    if request.method == "POST":

        if request.form.get("date") == "":
           return apology("No datetime selected", 400)
        if request.form.get("city") == "":
            return apology("Need to enter the cityname", 400)

        main_city = request.form.get("city")
        main_city = main_city.split(",")[0]
        data = lookup(main_city)
        if data == None:
            return apology("No City like that", 400)
        #Enquiry if User has phone number in case of text
        value = request.form.get("value")
        if value == "1": value = "email"
        elif value == "3": value = "text"
        elif value == "2":
            return apology("Need to select reminder type", 400)

        cityname = data["location"]["name"]
        datetime = request.form.get("date")
        date = datetime.split("T")[0]
        time = datetime.split("T")[1]
        db.execute("INSERT INTO reminders (user_id, type, reminder_status, datetime, date, time, cityname) VALUES(?, ?, ?, ?, ?, ?, ?)", user_id, value, True, datetime, date, time, cityname)
        return redirect("/history")
    else:
        reminders = db.execute("SELECT * FROM reminders WHERE user_id = ?;", user_id)
        cityname = None
        if len(reminders) == 1:
            cityname = db.execute("SELECT cityname FROM reminders WHERE user_id = ?;", user_id)[0]["cityname"]
        return render_template("reminder.html", cityname = cityname)


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    userid = session["user_id"]
    main_city = db.execute("SELECT main_city FROM users WHERE id = ?;", userid)
    if main_city[0]["main_city"] == None:
        main_city[0]["main_city"] = "London"

    data = lookup(main_city[0]["main_city"])
    if data == None:
        return apology("No City like that", 400)

    hourlist = []
    for number in range(23):
        if data["forecast"]["hour"][number]["will_it_rain"] == 1:
            temp = { number : data["forecast"]["hour"][number]["chance_of_rain"] }
            hourlist.append(temp.copy())

    for number in range(1, 24):
        if( number % 6 == 0 or number == 23):
            data["forecast"]["hour"][number]["time"] = data["forecast"]["hour"][number]["time"].replace(data["forecast"]["date"], "")
    return render_template("index.html", data=data, hourlist = hourlist)

@app.route("/phone_change", methods=["GET", "POST"])
@login_required
def phone_change():
    if request.method == "POST":
        if not request.form.get("phone_number"):
            return apology("Must provide phone number", 403)
        phone_number = request.form.get("phone_number")
        db.execute("UPDATE users SET phone_number = ? WHERE id = ?", phone_number, session["user_id"])
        return redirect("/history")
    else:
        user_id = session["user_id"]
        phone_number = db.execute("SELECT phone_number FROM users WHERE id = ?;", user_id)[0]["phone_number"]
        return render_template("phone_change.html", phone_number = phone_number)


@app.route("/city_change", methods=["GET", "POST"])
@login_required
def city_change():
    if request.method == "POST":
        if not request.form.get("city"):
            return apology("must provide City name", 403)
        main_city = request.form.get("city")
        main_city = main_city.split(",")[0]
        data = lookup(main_city)
        if data == None:
            return apology("No weather for city like that", 400)


        else:
            db.execute("UPDATE users SET main_city = ? WHERE id = ?", main_city, session["user_id"])
            return redirect("/")
    else:
        return render_template("city_change.html")

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        if not request.form.get("password"):
            return apology("must provide old password", 403)

        # Ensure password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide new password", 403)

        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)

        if request.form.get("new_password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid old password", 403)
        else:
            password_hash = generate_password_hash(request.form.get("new_password"))
            db.execute("UPDATE users SET hash = ? WHERE id = ?", password_hash, session["user_id"])
            return redirect("/login")
    else:
        return render_template("change.html")


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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords must match", 400)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return apology("Username already exists", 400)

        username = request.form.get("username")
        password_hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password_hash)

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


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
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        symbol = request.form.get("symbol")
        symbol = symbol.split(",")[0]
        data = lookup(symbol)

        if data == None:
            return apology("No weather for city like that", 400)
        if data == None:
            return apology("No City like that", 400)
        hourlist = []
        for number in range(23):
            if data["forecast"]["hour"][number]["will_it_rain"] == 1:
                temp = { number : data["forecast"]["hour"][number]["chance_of_rain"] }
                hourlist.append(temp.copy())

        return render_template("quoted.html", data=data, hourlist = hourlist)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
