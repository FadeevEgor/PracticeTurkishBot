from enum import Enum
from pathlib import Path 
import string

import flask
import functions_framework
from telegram import Bot, User
from telegram.constants import ParseMode
from emoji import emojize

from router import RequestRouter, CommandRouter, Response
from telegram_bot import bot_from_config, send_text, parse_command
from user_token import UsersTable, get_token
from translation import Translator, Language


class Emojies(str, Enum):
    russia = emojize(":Russia:")
    turkiye = emojize(":Turkey:")
    england = emojize(":England:")
    awkward = emojize(":downcast_face_with_sweat:")


lang_to_flag = {
    Language.russian: Emojies.russia,
    Language.english: Emojies.england,
    Language.turkish: Emojies.turkiye
}


request_routes = RequestRouter()
command_routes = CommandRouter()
bot = bot_from_config()
user_table = UsersTable.from_config()
translator = Translator.from_config()
templates_folder = Path("templates")


@command_routes.command("/about")
def command_about(bot: Bot, user: User) -> None:
    with open(templates_folder/"about.md", encoding="utf-8") as f:
        send_text(bot, user.id, f.read(), parse_mode=ParseMode.MARKDOWN_V2)
    command_routes.direct("/id", bot, user)
    command_routes.direct("/token", bot, user)
    
    
@command_routes.command("/start")
def command_start(bot: Bot, user: User) -> None:
    send_text(bot, user.id, fr"Привет, {user.first_name}\!")
    command_routes.direct("/about", bot, user)
    command_routes.direct("/config", bot, user)
    
@command_routes.command("/id")
def command_id(bot: Bot, user: User) -> None:
    send_text(bot, user.id, f"Твой id: `{user.id}`", parse_mode=ParseMode.MARKDOWN_V2)

@command_routes.command("/token")
def command_token(bot: Bot, user: User) -> None:
    token = get_token(user_table, user.id)
    send_text(bot, user.id, f"Твой токен: `{token}`", parse_mode=ParseMode.MARKDOWN_V2)

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
    send_text(bot, user.id, first_message, parse_mode=ParseMode.MARKDOWN_V2)
    send_text(bot, user.id, second_message, parse_mode=ParseMode.MARKDOWN_V2)

def get_translation(text: str) -> str:
    src, *translations = translator.translate(text)
    if src is None:
        return f"Не смог распознать язык {Emojies.awkward}."
    
    src_flag = lang_to_flag[src]
    result = f'Перевод для "<b>{text}</b>".\nУгаданный язык: {src_flag}.\n\n'
    for t in translations:
        if not any([t.demek, t.glosbe, t.google]):
            continue
        
        dst_flag = lang_to_flag[t.language]
        result += f"{src_flag} -> {dst_flag}:\n"
        if t.demek is not None:
            result += f"<b>demek.ru</b>: {t.demek}.\n"
        if t.glosbe is not None:
            result += f"<b>glsobe.com</b>: {t.glosbe}.\n"
        if t.google is not None:
            result += f"<b>translate.google.com</b>: {t.google}.\n"
        result += "\n"
    return result


@request_routes.route("/webhook")
def webhook(request: flask.Request) -> Response:
    user, text, commands = parse_command(request.data, bot)
    print(user, text, commands)
    if user is None:
        return "Unexpected request from telegram", 200
    if text is not None and text != "":
        translation = get_translation(text)
        send_text(bot, user.id, translation, parse_mode=ParseMode.HTML)
    for command in commands:
        command_routes.direct(command, bot, user)
    return "Ok", 200


@request_routes.route("/")
def status(request: flask.Request) -> Response:
    return """<title>PracticeTurkishBot</title>
    <H1>The bot is online</H1>
    """, 200

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
