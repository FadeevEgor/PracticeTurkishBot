from pathlib import Path 
import string

import flask
import functions_framework
from telegram import Bot, User
from telegram.constants import ParseMode

from database import UsersTable
from router import RequestRouter, CommandRouter, Response
from telegram_bot import bot_from_config, send_text, parse_message
from translation import Translator, get_translation


request_routes = RequestRouter()
command_routes = CommandRouter()
bot = bot_from_config()
user_table = UsersTable.from_config()
templates_folder = Path("templates")
translator = Translator()


@command_routes.command("/about")
def command_about(bot: Bot, user: User) -> None:
    "Generates response message to the command `/about`"
    with open(templates_folder/"about.md", encoding="utf-8") as f:
        send_text(bot, user.id, f.read(), parse_mode=ParseMode.MARKDOWN_V2)
    
@command_routes.command("/start")
def command_start(bot: Bot, user: User) -> None:
    "Generates response message to the command `/start`"
    send_text(bot, user.id, fr"Привет, {user.first_name}!")
    command_routes.direct("/about", bot, user) 
    
@command_routes.command("/id")
def command_id(bot: Bot, user: User) -> None:
    "Generates response message to the command `/id`"
    send_text(bot, user.id, f"Твой id: `{user.id}`", parse_mode=ParseMode.MARKDOWN_V2)

@command_routes.command("/token")
def command_token(bot: Bot, user: User) -> None:
    "Generates response message to the command `/token`"
    token = user_table.get_token(user.id)
    send_text(bot, user.id, f"Твой токен: `{token}`", parse_mode=ParseMode.MARKDOWN_V2)

@command_routes.command("/config")
def command_config(bot: Bot, user: User) -> None:
    "Generates response message to the command `/config`"
    with open(templates_folder/"config.md", encoding="utf-8") as f:
        first_message = f.read()
    
    with open(templates_folder/"config_template.md", encoding="utf-8") as f:
        template = string.Template(f.read())
    second_message = template.substitute({
        "id": user.id,
        "token": user_table.get_token(user.id)
    })
    send_text(bot, user.id, first_message, parse_mode=ParseMode.MARKDOWN_V2)
    send_text(bot, user.id, second_message, parse_mode=ParseMode.MARKDOWN_V2)

@command_routes.command("/subscribe")
def subscribe(bot: Bot, user: User) -> None:
    user_table.subscribe(user.id)
    message = 'Вы подписались на "слова дня"!'
    send_text(bot, user.id, message)

@command_routes.command("/unsubscribe")
def subscribe(bot: Bot, user: User) -> None:
    user_table.unsubscribe(user.id) 
    message = 'Вы отписались от "слова дня"!'
    send_text(bot, user.id, message)

@request_routes.route("/webhook")
def webhook(request: flask.Request) -> Response:
    """
    This route is used as telegram webhook.
    All messages to the bot are processed here.
    """
    user, text, commands = parse_message(request.data, bot)
    print(user, text, commands)
    if user is None:
        return "Unexpected request from telegram", 200
    if text is not None and text != "":
        translation = get_translation(translator, text)
        send_text(bot, user.id, translation, parse_mode=ParseMode.HTML)
    for command in commands:
        command_routes.direct(command, bot, user)
    return "Ok", 200

@request_routes.route("/external")
def external(request: flask.Request) -> Response:
    """
    Currently used only to send mistakes from CLI-application session.
    Checks user tokens in order to validate owner.
    """
    data = request.form
    user_id = int(data["user id"])
    text = data["text"]
    token = data["token"]
    
    if user_table.check_token(user_id, token): 
        send_text(bot, user_id, text)
        return "Message sent", 200
    print("Wrong token")
    return "Wrong token.", 403

@request_routes.route("/")
def status(request: flask.Request) -> Response:
    "Allows to check the google function status via get request"
    return """<title>PracticeTurkishBot</title>
    <H1>The bot is online</H1>
    """, 200

@functions_framework.http
def http(request: flask.Request):
    """
    The entry point for google functions framework.
    Redirects request based on the its path via RequestRouter.
    """
    path = request.path
    return request_routes.direct(path, request)
