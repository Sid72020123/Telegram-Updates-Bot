"""
Telegram Updates Bot - Main
---------------------------
A personal Telegram bot to send updates such as daily weather, facts, etc. to the owner at a specified time!
NOTE: This code will allow only the owner of the bot (i.e., a single person to use it). See the Config file. However, this code can be changed to allow more people to access this bot...

Also, a lot of code from the files of this project can be improved and there are many in-built functions to do so.
-----
Code by: @Sid72020123 on Github
"""

"""
These are the contents of the updates.json file:
[
    {
        "id": "wu",
        "name": "Weather Updates",
        "settings": {
            "time": "21:30:00",
            "city": ""
        }
    },
    {
        "id": "dq",
        "name": "Daily Quotes",
        "settings": {
            "time": "06:00:00"
        }
    },
    {
        "id": "nf",
        "name": "Number Facts",
        "settings": {
            "time": "20:55:00"
        }
    }
]
"""

# --- Imports ---
from json import loads, dumps
from threading import Thread

from Config import BOT_TOKEN, OWNER_TELEGRAM_ID
from TelegramAPI import TelegramBot, InlineKeyboardInput
from APIs import schedule_loop, update_settings

# --- Main Code ---
bot = TelegramBot(BOT_TOKEN)  # Main bot object

COMMANDS = {
    "start": "Just sends a start message",
    "help": "Shows this help message",
    "credits": "Shows the credits and the services used by this bot",
    "edit_updates": "Edit the settings of the updates you receive",
    "cancel": "Cancel the current operation"
}  # List of all commands

# A more efficient method would be to create a function for the code below as it's repeated in other parts of the code:
ALL_UPDATES = loads(open("updates.json", "r").read())  # See the structure of the File above
UPDATES_IDS = {}
for update in ALL_UPDATES:
    UPDATES_IDS[update["id"]] = {"name": update["name"], "settings": update["settings"]}

# Unicode of Emojis used by the bot
hand_emoji = "\U0001F44B"
pencil_emoji = "\U0000270F"
message_emoji = "\U00002709"
warning_emoji = "\U000026A0"
question_emoji = "\U00002753"
success_emoji = "\U00002705"
cloud_emoji = "\U00002601"


# --- Bot Events ---
@bot.on_event("start")
def bot_start():
    print(f"[*] Bot Started!")


@bot.on_event("stop")
def bot_stop():
    print(f"[*] Bot Stopped!")


@bot.on_event("new_command")
def print_new_command_info(**data):
    command = data["command"]
    id = data["message"]["from"]["id"]
    username = data["message"]["from"].get("username", "(no username)")
    print(
        f"[*] New command: {command} -> {id} -> @{username}")  # Print the information of the user using the bot's command


# --- Bot Commands ---
@bot.on_command("<any>")
def check_user(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]

    if sender_id != OWNER_TELEGRAM_ID:  # Restrict the bot access so that only the owner can use it >:)
        bot_owner_data = bot.get_user_info(OWNER_TELEGRAM_ID)["result"]
        username_exists = True if 'username' in bot_owner_data else False
        owner_username = f"""{
        bot_owner_data['first_name']} (username doesn't exist)"""
        if username_exists:
            owner_username = f"@{bot_owner_data['username']}"
        bot.send_message(sender_id,
                         f"""{warning_emoji} <b>You are not allowed to access this bot!</b>\nThis bot is privately used by {
                         owner_username}""", parse_mode="HTML")
        return False  # Disallow Access
    return True  # Allow Access


@bot.on_command("start")
def start(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]
    bot.send_message(sender_id, f"""{hand_emoji} <b>Hello, <i>{
    sender['first_name']}</i>!</b>\n\nI'm <i>Daily Updates Bot</i>! I send many kinds of updates (or information from the internet) automatically at a specified time to my owner!\n\n<i>Use the /help command to see the list of available commands</i>""",
                     parse_mode="HTML")


@bot.on_command("help")
def help(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]
    string = ""
    i = 1
    for command in COMMANDS:
        string += f"""{i}) <b>/{command}</b>: <i>{COMMANDS[command]}</i>\n"""
        i += 1
    bot.send_message(sender_id, f"""{pencil_emoji} <b>List of available commands:</b>\n\n{
    string}\n<i>To read the credits, use the /credits command</i>""", parse_mode="HTML")


@bot.on_command("credits")
def credits(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]
    message = f"""{pencil_emoji} <b>Credits:</b>\n\n<b>Bot made by <i>@siddheshdc</i></b>\n\n<i>Use the /help command to see the list of available commands</i>"""
    bot.send_message(sender_id, message, parse_mode="HTML")


editing = {}

empty_menu = InlineKeyboardInput("empty")

main_menu = InlineKeyboardInput("main")
main_menu.add_button("Weather Updates", "wu")
main_menu.add_button("Daily Quotes", "dq")
main_menu.add_button("Number Facts", "nf")
main_menu.add_button("< Cancel >", "cancel")


def cancel_keyboard_inputs(sender_id, message_id):
    """
    Edit the contents of the keyboard input of a Telegram message to an empty menu
    """
    bot.edit_message(sender_id, message_id, f"{success_emoji} Successfully cancelled the current operation!",
                     parse_mode="HTML")
    bot.edit_input_keyboard_input(sender_id, message_id, empty_menu)


def ask_time(**data):
    """
    Time validation script
    """
    sender = data["message"]["from"]
    sender_id = sender["id"]
    message_text = data["message"]["text"]
    message_text = message_text.strip()
    ui = editing[sender_id]
    try:
        if len(message_text) != 5 or ":" not in message_text:
            message = f"""{warning_emoji} <b>Can't change the time</b>\n\nPlease send the time in required format. Enter the time again!\n\n<i>Use the /cancel command to cancel the current operation</i>"""
            bot.send_message(sender_id, message, parse_mode="HTML")
        else:
            t = message_text.split(":")
            if not (t[0].isdigit() and t[1].isdigit()):
                message = f"""{warning_emoji} <b>Can't change the time</b>\n\nPlease send the time in required format. Enter the time again!\n\n<i>Use the /cancel command to cancel the current operation</i>"""
                bot.send_message(sender_id, message, parse_mode="HTML")
            else:
                index = 0
                for u in ALL_UPDATES:
                    if u["id"] == editing[sender_id]:
                        index = ALL_UPDATES.index(u)
                ALL_UPDATES[index]["settings"]["time"] = message_text + ":00"
                with open("updates.json", "w+") as file:
                    file.write(dumps(ALL_UPDATES, indent=4))
                update_settings()
                message = f"""{success_emoji} <b>Successfully changed the time!</b>\n\nThe time of <i><u>{UPDATES_IDS[ui]["name"]}</u></i> is successfully changed to <i><u>{message_text}</u></i>!"""
                bot.send_message(sender_id, message, parse_mode="HTML")
                del bot.command_history[
                    sender_id]  # This is required whenever a function accepts an input to let the API wrapper know that the input work is finished...
    except Exception as E:
        message = f"""{warning_emoji} <b>Can't change the time</b>\n\nAn error occurred. Make sure that the time message sent by you is in the required format and then try again!\n\n<i><u>Error Message:</u>\n<blockquote>{E}</blockquote></i>\n\n<i>Use the /cancel command to cancel the current operation</i>"""
        bot.send_message(sender_id, message, parse_mode="HTML")


@bot.on_command("_prompt_time", accept_text_message=ask_time)
def prompt_time(**data):  # This is an empty function just used to accept user text inputs
    ...


def change_time(**data):
    callback_query = data["callback_query"]
    callback_query_id = data["callback_query_id"]
    sender_id = callback_query["from"]["id"]
    message_id = data["message_id"]
    input_data = data["input_data"]
    if bot.answer_callback_query(callback_query_id)[
        "ok"]:  # Make sure to call this answer_callback_query function to let the user know that the bot has received the button press response from the user
        if input_data == "cancel":  # When user presses "cancel" button
            cancel_keyboard_inputs(sender_id, message_id)
            if sender_id in editing:
                del editing[sender_id]
        elif input_data == "back":  # When user presses "Go back" button, edit the current keyboard menu with the main menu
            message = f"{pencil_emoji} <b>Edit the settings of the updates you receive:</b>\n\nSelect an option:"
            bot.edit_message(sender_id, message_id, message, parse_mode="HTML")
            bot.edit_input_keyboard_input(sender_id, message_id, main_menu)
        else:  # If the user has pressed other buttons
            id = input_data.split("_")
            if id[0] == "ct":
                editing[sender_id] = id[1]

                message = f"""{pencil_emoji} You chose to change the settings of <i>{UPDATES_IDS[id[1]]["name"]}</i>..."""
                bot.edit_message(sender_id, message_id, message, parse_mode="HTML")
                bot.edit_input_keyboard_input(sender_id, message_id, empty_menu)

                ui = editing[sender_id]
                message = f"""{pencil_emoji} <b>Change the time of <i>{UPDATES_IDS[ui]["name"]}</i></b>:\n\nEnter the time in 24 hour clock format seperated by a colon(:)\n\n<i><u>Note:</u>\nIf the hour or minute is single digit, prefix it with a zero. \nEg.,\n<blockquote>For 9:30 am use, 09:30</blockquote>\n<blockquote>For 9:30 pm use, 21:30</blockquote></i>\n\n<i>Use the /cancel command to cancel the current operation</i>"""
                bot.send_message(sender_id, message, parse_mode="HTML")

                bot.command_history[
                    sender_id] = "_prompt_time"  # Set the pseudo command so that the bot will receive the text inputs...


def change_settings(**data):
    callback_query = data["callback_query"]
    callback_query_id = data["callback_query_id"]
    sender_id = callback_query["from"]["id"]
    message_id = data["message_id"]
    input_data = data["input_data"]
    if bot.answer_callback_query(callback_query_id)["ok"]:
        if input_data == "cancel":
            cancel_keyboard_inputs(sender_id, message_id)
        else:
            settings_string = ""
            for setting in UPDATES_IDS[input_data]["settings"]:
                settings_string += f"<b><u>{setting.title()}</u></b>: <i>{UPDATES_IDS[input_data]['settings'][setting]}</i>\n"
            message = f"""{pencil_emoji} <b>Edit the settings of {UPDATES_IDS[input_data]["name"]}:</b>\n\n{settings_string}\nChoose an option:"""

            change_menu = InlineKeyboardInput("change")
            change_menu.add_button("Change Time", f"ct_{input_data}")
            change_menu.add_button("< Go Back >", "back")
            change_menu.add_button("< Cancel >", "cancel")
            change_menu.set_action_function(change_time)

            bot.edit_message(sender_id, message_id, message, parse_mode="HTML")
            bot.edit_input_keyboard_input(sender_id, message_id, change_menu)
    else:
        pass


main_menu.set_action_function(change_settings)  # This is required for the main menu to work properly


@bot.on_command("edit_updates")
def edit_updates(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]
    message = f"{pencil_emoji} <b>Edit the settings of the updates you receive:</b>\n\nSelect an option:"
    bot.send_inline_keyboard_input(
        sender_id, message, main_menu, parse_mode="HTML")


@bot.on_command("cancel")
def cancel(**data):
    sender = data["message"]["from"]
    sender_id = sender["id"]

    if sender_id in bot.command_history:
        del bot.command_history[
            sender_id]  # This stops the custom API wrapper from further accepting text inputs from the user
        message = f"{success_emoji} Successfully cancelled the operation of the previous command '<i>{bot.previous_command[sender_id]}</i>'!"
    else:
        message = f"""{question_emoji} No ongoing operation found to cancel it..."""
    bot.send_message(sender_id, message, parse_mode="HTML")


def main():
    """
    The main function to start all the essential threads and the polling loop of the bot
    """
    Thread(target=schedule_loop, args=(bot, OWNER_TELEGRAM_ID,)).start()
    bot.start_polling()


if __name__ == "__main__":
    main()
