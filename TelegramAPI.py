"""
Telegram Updates Bot - Telegram API Wrapper File
------------------------------------------------
This file contains the code to a custom Telegram API wrapper made specially for this project.
(I know there are many libraries out there but I still made this)

-----
Code by: @Sid72020123 on Github
"""

# --- Imports ---
from json import dumps
from requests import Session
from requests.exceptions import ConnectionError
from traceback import print_exc

TELEGRAM_API_URL = "https://api.telegram.org/bot"  # This is the root endpoint of Telegram API


# --- Main Code ---
class InlineKeyboardInput:
    def __init__(self, name):
        """
        The inline keyboard input class to make things easier later in the code...
        :param name: Unique name so that while parsing the user message, the wrapper will understand which buttons are exactly pressed by the user
        """
        self.name = name
        self.buttons = []
        self.action_function = None

    def set_action_function(self, func):
        """
        THe function to call when the user presses a button
        :param func: Any function
        """
        self.action_function = func

    def add_button(self, text: str, callback_data: str):
        """
        Add
        :param text: Any string text for the button
        :param callback_data: Unique identifier for a specific button so that the wrapper will tell which button is exactly pressed
        """
        # NOTE 1: There are many button actions in Telegram, but I'm using some basic ones as per the requirements of this project
        # NOTE 2: There a way to group the inline keyboard buttons in Telegram by keeping the buttons of the same group together in a list...
        self.buttons.append([{"text": text, "callback_data": f"{self.name}_{callback_data}"}])


class TelegramBot:
    def __init__(self, token):
        """
        The Main Bot code
        :param token: Telegram Bot API Token
        """
        self.session = Session()
        self.bot_token = token
        self.api_url = f"{TELEGRAM_API_URL}{token}"
        self.commands = {}
        self.commands_accept_text_responses = {}  # To keep the track of which commands accept text responses after the user has used them
        self.command_history = {}
        self.previous_command = {}
        self.inline_keyboard_inputs = {}

        self.events = {"start": None, "new_message": None,
                       "new_command": None, "stop": None}

        # The code below is required to keep track of the updates (or messages) the bot receives
        try:
            open("update_id.txt")
        except FileNotFoundError:
            file = open("update_id.txt", "w")
            file.write("0")
            file.close()
        prev_id = int(open("update_id.txt", "r").read())
        r = self.get_updates(offset=-1)["result"]
        if len(r) > 0:
            u = r[0]
            new_id = u["update_id"]
            if new_id > prev_id:
                self.increment_update_id(new_id)

    def get_updates(self, timeout: int = 3, limit: int = 10, offset: int = -1):
        return self.session.get(f"{self.api_url}/getUpdates",
                                params={"limit": limit, "offset": offset, "timeout": timeout}).json()

    def send_message(self, chat_id, message: str, parse_mode: str = "MarkdownV2"):
        # I know I should have set "HTML" as the default parse_mode value as all the messages sent by this bot are in HTML format.
        return self.session.get(f"{self.api_url}/sendMessage",
                                params={"chat_id": chat_id, "parse_mode": parse_mode, "text": message,
                                        "disable_web_page_preview": True}).json()

    def edit_message(self, chat_id, message_id, message: str, parse_mode: str = "MarkdownV2"):
        payload = {"chat_id": chat_id, "message_id": message_id, "parse_mode": parse_mode, "text": message,
                   "disable_web_page_preview": True}
        return self.session.get(f"{self.api_url}/editMessageText", params=payload).json()

    def send_inline_keyboard_input(self, chat_id, message, iki: InlineKeyboardInput, parse_mode: str = "MarkdownV2"):
        payload = {"chat_id": chat_id, "parse_mode": parse_mode, "text": message,
                   "disable_web_page_preview": True, "reply_markup": dumps({"inline_keyboard": iki.buttons})}
        self.inline_keyboard_inputs[iki.name] = iki
        return self.session.get(f"{self.api_url}/sendMessage", params=payload).json()

    def edit_input_keyboard_input(self, chat_id, message_id, iki: InlineKeyboardInput):
        payload = {"chat_id": chat_id, "message_id": message_id,
                   "reply_markup": dumps({"inline_keyboard": iki.buttons})}
        if len(iki.buttons) == 0:
            payload["reply_markup"] = {}
        self.inline_keyboard_inputs[iki.name] = iki
        return self.session.get(f"{self.api_url}/editMessageReplyMarkup", params=payload).json()

    def get_user_info(self, id: int):
        return self.session.get(f"{self.api_url}/getChat?chat_id={id}").json()

    def on_command(self, commmand_name, accept_text_message=None):
        if accept_text_message is not None:
            self.commands_accept_text_responses[commmand_name] = accept_text_message

        def func(f):
            self.commands[commmand_name] = f

        return func

    def on_event(self, event_name):
        def func(f):
            self.events[event_name] = f

        return func

    def _emit_event(self, name, **data):
        if self.events[name] is not None:
            self.events[name](**data)

    def answer_callback_query(self, query_id: int):
        data = {"callback_query_id": query_id}
        return self.session.get(f"{self.api_url}/answerCallbackQuery", data=data).json()

    def increment_update_id(self, prev_id):
        new = prev_id + 1
        with open("update_id.txt", "w+") as file:
            file.write(str(new))
        return new

    def cancel_command_text_inputs(self, chat_id):
        try:
            del self.command_history[chat_id]
        except:
            pass

    def start_polling(self):
        try:
            file = open("update_id.txt", "r")
            UPDATE_ID = int(file.read())
            file.close()
        except Exception as E:
            print(f"TelegramAPI: Error while reading previous update ID: {E}")
            return None
        self._emit_event("start")
        while True:
            try:
                raw_update = self.get_updates(offset=UPDATE_ID)
                if raw_update["ok"]:
                    if len(raw_update["result"]) != 0:
                        raw_message = raw_update["result"][0]
                        if "message" in raw_message:  # New Message
                            message = raw_message["message"]
                            self._emit_event("new_message", message=message)
                            chat_id = message["from"]["id"]
                            if "entities" in message:
                                entity_type = message["entities"][0]["type"]
                                if entity_type == "bot_command":
                                    text = message["text"]
                                    command = text[1:]
                                    if command in self.commands:
                                        self._emit_event("new_command", command=command, message=message)
                                        proceed = True
                                        if "<any>" in self.commands:
                                            proceed = self.commands["<any>"](message=message)
                                        if proceed:
                                            if command in self.commands_accept_text_responses:
                                                self.command_history[chat_id] = command
                                            else:
                                                if chat_id in self.command_history and (self.previous_command[
                                                                                            chat_id] in self.commands_accept_text_responses):
                                                    del self.command_history[
                                                        chat_id]  # Remove the command from history so that the bot won't continue to keep taking text user responses even after the command's script was successfully run...
                                            self.commands[command](message=message)
                                            self.previous_command[chat_id] = command
                            else:  # For the text input after the user has used a specific command
                                if chat_id in self.command_history:
                                    command_used = self.command_history[chat_id]
                                    if command_used in self.commands_accept_text_responses:
                                        self.commands_accept_text_responses[command_used](
                                            message=message)
                            UPDATE_ID = self.increment_update_id(
                                int(raw_message["update_id"]))
                        elif "callback_query" in raw_message:  # Callback query updates (or inline keyboard updates in case of this project)
                            callback_query = raw_message["callback_query"]
                            call_back_query_id = callback_query["id"]
                            callback_data = callback_query["data"]
                            chat_id = callback_query["message"]["chat"]["id"]
                            message_id = callback_query["message"]["message_id"]
                            input_name = callback_data.split("_")[0]
                            input_data = callback_data[callback_data.index(
                                "_") + 1:]
                            data = {
                                "callback_query": callback_query,
                                "callback_query_id": call_back_query_id,
                                "callback_data": callback_data,
                                "chat_id": chat_id,
                                "message_id": message_id,
                                "input_name": input_name,
                                "input_data": input_data
                            }
                            if self.inline_keyboard_inputs[input_name].action_function is not None:
                                self.inline_keyboard_inputs[input_name].action_function(
                                    **data)
                            else:
                                self.answer_callback_query(call_back_query_id)
                            UPDATE_ID = self.increment_update_id(
                                int(raw_message["update_id"]))
            except ConnectionError:
                pass
            except KeyboardInterrupt:
                self._emit_event("stop")
                break
            except Exception as E:
                print(f"TelegramAPI: Polling Loop Error - {E}")
                print_exc()
                UPDATE_ID = self.increment_update_id(
                    UPDATE_ID)  # Ignore the new message
