# Rain?

#### Description:
Rain? is Flask Webapp that as a goal has a daily reminder of whether it is gonna rain or not and when, at the specified by the user time, and by specified medium of contact.
Rain? uses WeatherApi to collect the Weather data and converts its useful parts from JSONs to Python Dictionaries that are later used in HTML forms by application of Jinja

Rain? uses SQLite Databe, that stores 2 tables users and reminders
Reminders table has its own id that is a primary key but it also stores user_id, what allows accessing the users table, based on the user id

Rain? runs a scheudler every minute, that makes SQL Querry to the database reminders table, determining whether there are any reminders that are due, and if so
it sends the reminders based on the user's medium of choice, followed by UPADE querry to the db, updating the reminder's status

The WebApp uses Google Places Api that allows it to have Auto-Fill for the cities and then formats the form output in Python, making a Querry to WeatherAPI and if the place
exist then storing it in users table database, based on the logged user.
In addition to WeatherAPI and Google Places, the Webapp uses Vonage api that allows its text messaging functionality.

### Configuration:

#### APIs and Keys
1. Create Gmail Account
2. Enable Access for less secure apps
3. Create Google API Key, Enable Places API
4. In Templates/Layout.html on line 6 add your Google API Key, as specified:
<script src="https://maps.googleapis.com/maps/api/js?key=PLACE_FOR_YOUR_API_KEY&libraries=places"></script>

5. Create Weather API Account weatherapi.com
6. Get the API KEY
7. Paste API KEY to api_key variable in helpers.py Line 8

8. Create Vonage Account: https://dashboard.nexmo.com/
9. Get Vonage API KEY
10. From https://dashboard.nexmo.com/getting-started/sms, Get the line with:
client = vonage.Client(key="YOUR KEY", secret="SECRET")
Containig your API KEY and fill it in application.py on line 36 and 37 in places of vonage_key and vonage_secret

#### SQLite Database Setup
Database name: weather.db

Two tables in Databese:
CREATE TABLE 'users' (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL, 'main_city' text, 'phone_number' integer DEFAULT NULL, PRIMARY KEY(id))
CREATE TABLE 'reminders' ('id' integer PRIMARY KEY NOT NULL, 'user_id' integer NOT NULL, 'type' text NOT NULL, 'reminder_status' boolean NOT NULL DEFAULT false, 'sent_status' boolean NOT NULL DEFAULT false,'datetime' datetime NOT NULL, 'date' date NOT NULL, 'time' time NOT NULL, 'cityname' text NOT NULL )

#### Email Reminders:
In application.py starting from Line 25:
app.config["MAIL_DEFAULT_SENDER"] = "DEFAULT EMAIL RECIPIENT, WHEN UNSPECIFIED"
app.config["MAIL_USERNAME"] = "YOUR EMAIL ADDRESS"
app.config["MAIL_PASSWORD"] = "EMAIL PASSWORD"
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

