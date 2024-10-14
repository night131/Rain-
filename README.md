# Rain?

## About
Rain? is a Flask web app that sends personalized daily rain forecasts. It uses WeatherAPI for data, Google Places for locations, and SQLite for storage. Users set custom reminders delivered via email or SMS. An automated scheduler ensures timely notifications, helping users stay prepared for rainy days.

## Features
- Personalized rain forecasts
- Custom reminder settings
- Multiple notification methods (email, SMS)
- Location auto-fill using Google Places API
- Automated scheduling system

## Setup

### API Configuration
1. Create a Gmail account and enable access for less secure apps
2. Set up Google API Key and enable Places API
3. Create a WeatherAPI account (weatherapi.com) and get API key
4. Set up a Vonage account for SMS functionality

### Database Setup
- SQLite database (weather.db) with two tables: 'users' and 'reminders'

### Configuration Steps
1. In `templates/layout.html`, add your Google API Key:
   ```html
   <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"></script>
   ```
2. In `helpers.py`, add your WeatherAPI key:
   ```python
   api_key = "YOUR_WEATHER_API_KEY"
   ```
3. In `application.py`, add Vonage credentials:
   ```python
   client = vonage.Client(key="YOUR_VONAGE_KEY", secret="YOUR_VONAGE_SECRET")
   ```
4. Configure email settings in `application.py`:
   ```python
   app.config["MAIL_DEFAULT_SENDER"] = "DEFAULT_EMAIL"
   app.config["MAIL_USERNAME"] = "YOUR_EMAIL"
   app.config["MAIL_PASSWORD"] = "YOUR_PASSWORD"
   app.config["MAIL_PORT"] = 587
   app.config["MAIL_SERVER"] = "smtp.gmail.com"
   app.config['MAIL_USE_TLS'] = True
   app.config['MAIL_USE_SSL'] = False
   ```
