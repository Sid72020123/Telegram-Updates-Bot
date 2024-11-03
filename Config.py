"""
Telegram Updates Bot - Configuration File
-----------------------------------------
This file contains many variables used by the project

-----
Code by: @Sid72020123 on Github
"""

# --- Imports ---
from os import getenv
from dotenv import load_dotenv
from pytz import timezone

# --- Main Code ---
load_dotenv()  # Load the variables from the .env file
# This is the .env file:
"""
BOT_TOKEN=
OWNER_TELEGRAM_ID=
WEATHER_API_KEY=
"""

BOT_TOKEN = getenv("BOT_TOKEN", "")  # Telegram Bot Token
OWNER_TELEGRAM_ID = int(getenv("OWNER_TELEGRAM_ID", "0"))  # The Telegram ID of the person receiving the updates
TIMEZONE = timezone(
    "Asia/Kolkata")  # This world has many timezones. I live in this part and the free server is hosting the code somewhere in the other part...
WEATHER_API_URL = "https://api.weatherapi.com/v1"  # Weather Data Service API URL
WEATHER_API_KEY = getenv("WEATHER_API_KEY", "")  # The API key for the above API
