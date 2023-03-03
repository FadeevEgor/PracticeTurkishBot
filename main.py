from pathlib import Path 
import string

import flask
import functions_framework
from telegram import Bot, User

from router import RequestRouter, CommandRouter, Response
from telegram_bot import bot_from_config, send_text, parse_command
from user_token import UsersTable, get_token 

request_routes = RequestRouter()
command_routes = CommandRouter()
bot = bot_from_config()
user_table = UsersTable.from_config()
templates_folder = Path("templates")


@command_routes.command("/about")
def command_about(bot: Bot, user: User) -> None:
    with open(templates_folder/"about.md", encoding="utf-8") as f:
        send_text(bot, user.id, f.read(), markdown=True)
    command_routes.direct("/id", bot, user)
    command_routes.direct("/token", bot, user)
    
    

@command_routes.command("/start")
def command_start(bot: Bot, user: User) -> None:
    send_text(bot, user.id, fr"Привет, {user.first_name}\!")
    command_routes.direct("/about", bot, user)
    command_routes.direct("/config", bot, user)
    
    
@command_routes.command("/id")
def command_id(bot: Bot, user: User) -> None:
    send_text(bot, user.id, f"Твой id: `{user.id}`", markdown=True)

@command_routes.command("/token")
def command_token(bot: Bot, user: User) -> None:
    token = get_token(user_table, user.id)
    send_text(bot, user.id, f"Твой токен: `{token}`", markdown=True)

@command_routes.command("/config")
def command_config(bot: Bot, user: User) -> None:
    with open(templates_folder/"config.md", encoding="utf-8") as f:
        first_message = f.read()
    with open(templates_folder/"config_template.md", encoding="utf-8") as f:
        template = string.Template(f.read())
    
    second_message = template.substitute({
        "id": user.id,
        "token": get_token(user_table, user.id)
    })
    send_text(bot, user.id, first_message, markdown=True)
    send_text(bot, user.id, second_message, markdown=True)
  

@request_routes.route("/webhook")
def webhook(request: flask.Request) -> Response:
    user, commands = parse_command(request.data, bot)
    if user is None:
        return "Unexpected request from telegram", 200 
    for command in commands:
        command_routes.direct(command, bot, user)
    return "Ok", 200

@request_routes.route("/")
def status(request: flask.Request) -> Response:
    return "<H1>The bot is online</H1>", 200

@request_routes.route("/external")
def external(request: flask.Request) -> Response:
    data = request.form
    user_id = int(data["user id"])
    text = data["text"]
    token = data["token"]
    true_token = get_token(user_table, user_id)
    if token == true_token: 
        send_text(bot, user_id, text)
        return "Message sent", 200
    return "Wrong token.", 403

@functions_framework.http
def http(request: flask.Request):
    path = request.path
    return request_routes.direct(path, request)
