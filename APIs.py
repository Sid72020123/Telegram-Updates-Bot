"""
Telegram Updates Bot - API File
-------------------------------
This file contains the code to request the data from various sources (or APIs) sent by the bot

-----
Code by: @Sid72020123 on Github
"""

# --- Imports ---
import time
from json import loads
from requests import get
import arrow
from threading import Thread

from Config import WEATHER_API_URL, WEATHER_API_KEY, TIMEZONE

# --- Main Code ---
# Unicode of some required emojis
message_emoji = "\U00002709"
warning_emoji = "\U000026A0"
question_emoji = "\U00002753"
success_emoji = "\U00002705"
cloud_emoji = "\U00002601"

ALL_UPDATES = loads(open("updates.json", "r").read())
UPDATES_IDS = {}
for update in ALL_UPDATES:
    UPDATES_IDS[update["id"]] = {"name": update["name"], "settings": update["settings"]}

CITY = str(UPDATES_IDS["wu"]["settings"]["city"]).lower()  # City for the weather API

GROUPED_UPDATES = {}


def group_equal_times():
    """
    This function groups the schedule times together in a list
    """
    global GROUPED_UPDATES
    result = {}
    for i in UPDATES_IDS:
        t = UPDATES_IDS[i]["settings"]["time"]
        if t in result:
            result[t].append(i)
        else:
            result[t] = [i]
    GROUPED_UPDATES = result


def get_weather_forecast(d):
    """
    Get the weather forcast from the API
    :param d: The date
    (BTW, I only needed the data of the chances of rain but still, you can add more data)
    """
    try:
        raw_data = get(
            f"{WEATHER_API_URL}/forecast.json?q={CITY}&days=3&key={WEATHER_API_KEY}").json()
        forecasts = raw_data["forecast"]["forecastday"]
        for forecast in forecasts:
            if d == forecast["date"]:
                return [True, [forecast["day"]["daily_will_it_rain"], forecast["day"]["daily_chance_of_rain"]]]
        return [False, f"No data found for the date: {d}"]
    except Exception as E:
        return [False, E]


def send_weather_update(bot, sender_id):
    """
    Send the weather update message
    :param bot: The object of TelegramBot class
    :param sender_id: The Telegram ID of the person using the bot or the person using the commands
    """
    date_today = arrow.now(TIMEZONE)
    date_tomorrow = date_today.shift(days=1)
    f = get_weather_forecast(date_tomorrow.strftime("%Y-%m-%d"))
    if f[0] is True:
        will_it_rain, chance_of_rain = f[1]
        temp = "will rain" if will_it_rain == 1 else "will not rain"
        w = f"""\n\n<b>{cloud_emoji} Daily Weather Forecast:</b>\n\nTomorrow in <i>{CITY.title()}</i>, it <b><u>{temp}</u></b> with the chances of rain being <b><u>{
        chance_of_rain}%</u></b>\n\n<i>(Weather data was checked at {date_today.strftime('%d/%m/%Y %H:%M')})</i>"""
        bot.send_message(sender_id, w, parse_mode="HTML")
    else:
        print(
            f"WeatherAPI: Error while getting the weather - {f[1]}")


def send_daily_quotes(bot, sender_id):
    """
    Send the daily quotes message
    :param bot: The object of TelegramBot class
    :param sender_id: The Telegram ID of the person using the bot or the person using the commands
    """
    quote = get("https://zenquotes.io/api/today/").json()[0]
    message = f"""<b>{message_emoji} Daily Quote:</b>\n\n<blockquote>{quote["q"]} - <b>{
    quote["a"]}</b></blockquote>\n\n<i>Quotes fetched from <a href='https://zenquotes.io/'>ZenQuotes.io</a></i>"""
    bot.send_message(sender_id, message, parse_mode="HTML")


def send_number_fact(bot, sender_id):
    """
    Send the number facts message
    :param bot: The object of TelegramBot class
    :param sender_id: The Telegram ID of the person using the bot or the person using the commands
    """
    fact = get("http://numbersapi.com/random/math").text
    message = f"""<b>{message_emoji} Daily Number Fact:</b>\n\n<blockquote>{fact}</blockquote>\n\n<i>Facts fetched from <a href='http://numbersapi.com/'>NumbersAPI.com</a></i>"""
    bot.send_message(sender_id, message, parse_mode="HTML")


def update_settings():
    """
    This function just updates the variables when it's called so that the schedule loop can update the time automatically without re-running the code again...
    """
    global CITY
    global ALL_UPDATES
    global UPDATES_IDS
    global GROUPED_UPDATES
    global TIMES
    ALL_UPDATES = loads(open("updates.json", "r").read())
    UPDATES_IDS = {}
    for update in ALL_UPDATES:
        UPDATES_IDS[update["id"]] = {"name": update["name"], "settings": update["settings"]}

    CITY = str(UPDATES_IDS["wu"]["settings"]["city"]).lower()
    group_equal_times()
    TIMES = GROUPED_UPDATES.keys()


group_equal_times()
# Remember to keep the order of the list items in the following two variables same:
FUNCTIONS = [send_weather_update, send_daily_quotes, send_number_fact]
UPDATE_TYPES = ["wu", "dq", "nf"]

UPDATE_FUNCTIONS = {}
index = 0
for i in UPDATE_TYPES:
    UPDATE_FUNCTIONS[i] = FUNCTIONS[index]
    index += 1

TIMES = GROUPED_UPDATES.keys()


def schedule_loop(bot, sender_id):
    """
    The main loop to check the time and run each function according to the schedule
    :param bot: The object of TelegramBot class
    :param sender_id: The Telegram ID of the person using the bot or the person using the commands
    :return:
    """
    while True:
        try:
            current_time = arrow.now(TIMEZONE)
            current_hour = current_time.strftime("%H")
            current_minute = current_time.strftime("%M")
            current_second = current_time.strftime("%S")
            formatted_time = f"{current_hour}:{current_minute}:{current_second}"
            if formatted_time in TIMES:
                updates = GROUPED_UPDATES[formatted_time]
                for update in updates:
                    Thread(target=UPDATE_FUNCTIONS[update], args=(bot, sender_id,)).start()
        except Exception as E:
            print(f"[*] Error in Schedule Loop: {E}")
        time.sleep(1)
