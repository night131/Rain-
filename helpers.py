import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

api_key = "YOUR API KEY"

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(city):
    """Look up quote for symbol."""

    # Contact API
    try:
        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={urllib.parse.quote_plus(city)}&days=1"
        #url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "location" : { "name": quote["location"]["name"],
                            "region": quote["location"]["region"],
                            "country": quote["location"]["country"],
                            "time" : quote["location"]["localtime"]},

            "current" : { "text" : quote["current"]["condition"]["text"],
                        "icon" : quote["current"]["condition"]["icon"],
                        "temp_c" : quote["current"]["temp_c"]},
            "forecast" : quote["forecast"]["forecastday"][0]


            }
    except (KeyError, TypeError, ValueError):
        return None