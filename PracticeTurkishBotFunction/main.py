import asyncio
from pathlib import Path
import string
from typing import Any
from time import sleep

import functions_framework  # type: ignore
from flask import Request
from telegram import Bot, User  # type: ignore
from telegram.constants import ParseMode  # type: ignore
from httpx import AsyncClient  # type: ignore

from service import _Data
from database import UserTable
from languages import lowercase, detect_language
from router import RequestRouter
from telegram_bot.commands import BotCommands
from telegram_bot.api import (
    bot_from_config,
    send_text_async,
    answer_callback_query_and_remove_query,
    edit_keyboard,
)
from telegram_bot.parsing import parse_update, MessageContent, CallbackQueryContent
from translation import Translator
from morphology import Morphology
from utils import translate_and_send


templates_folder = Path("templates")
app = RequestRouter()
bot_commands = BotCommands()
bot = bot_from_config()
user_table = UserTable.from_config()
translator = Translator.from_config()
morphology = Morphology.from_config()


@bot_commands.command("/about")
async def command_about(bot: Bot, user: User) -> None:
    "Generates response messages to the command `/about`"
    for i in range(1, 4):
        with open(templates_folder / f"about_{i}.html", encoding="utf-8") as f:
            await send_text_async(bot, user.id, f.read(), ParseMode.HTML)
            sleep(0.5)


@bot_commands.command("/start")
async def command_start(bot: Bot, user: User) -> None:
    "Generates response message to the command `/start`"
    message = rf"Привет, {user.first_name}!"
    await send_text_async(bot, user.id, message)
    await command_about(bot, user)


@bot_commands.command("/id")
async def command_id(bot: Bot, user: User) -> None:
    "Generates response message to the command `/id`"
    message = f"Твой id: <code>{user.id}</code>."
    await send_text_async(bot, user.id, message, ParseMode.HTML)


@bot_commands.command("/token")
async def command_token(bot: Bot, user: User) -> None:
    "Generates response message to the command `/token`"
    token = user_table.get_token(user.id)
    message = f"Твой токен: <code>{token}</code>."
    await send_text_async(bot, user.id, message, ParseMode.HTML)


@bot_commands.command("/config")
async def command_config(bot: Bot, user: User) -> None:
    "Generates response message to the command `/config`"
    with open(templates_folder / "config.html", encoding="utf-8") as f:
        template = string.Template(f.read())
    message = template.substitute(
        {"id": user.id, "token": user_table.get_token(user.id)}
    )
    await send_text_async(bot, user.id, message, ParseMode.HTML)


@bot_commands.command("/subscribe")
async def subscribe(bot: Bot, user: User) -> None:
    user_table.subscribe(user.id)
    message = "Вы подписались на <b>слово дня</b>!"
    await send_text_async(bot, user.id, message, ParseMode.HTML)


@bot_commands.command("/unsubscribe")
async def unsubscribe(bot: Bot, user: User) -> None:
    user_table.unsubscribe(user.id)
    message = "Вы отписались от <b>слова дня</b>!"
    await send_text_async(bot, user.id, message, ParseMode.HTML)


async def process_message(bot: Bot, content: MessageContent) -> None:
    text = content.text
    user = content.user
    commands = content.commands
    if text is not None and text != "":
        text = lowercase(text, detect_language(text))
        async with AsyncClient() as client:
            message, available = await asyncio.gather(
                translate_and_send(translator, client, bot, user, text),
                morphology.available(client, text=text),
            )
        if available:
            keyboard = morphology.keyboard(text)
            await edit_keyboard(bot, user.id, message.id, keyboard)
    for command in commands:
        await bot_commands.dispatch(command, bot, user)


async def process_query(bot: Bot, content: CallbackQueryContent) -> None:
    user = content.user
    text = content.text
    query_id = content.query_id
    message_id = content.message_id
    async with AsyncClient() as client:
        _, analysis = await asyncio.gather(
            answer_callback_query_and_remove_query(bot, query_id, user.id, message_id),
            morphology.analyze(client, word=text),
        )
    if analysis is not None:
        await send_text_async(bot, user.id, analysis, ParseMode.HTML)


@app.route("/", "POST")
def webhook(data: _Data) -> Any:
    content = parse_update(data, bot)
    if content is None:
        return "Unexpected request from telegram", 200
    if isinstance(content, MessageContent):
        return asyncio.run(process_message(bot, content))
    if isinstance(content, CallbackQueryContent):
        return asyncio.run(process_query(bot, content))
    return "Unexpected request from telegram", 200


@app.route("/", "GET")
def status(_: _Data) -> str:
    "Allows to check the google function status via get request"
    return """<title>PracticeTurkishBot</title>
    <H1>The bot is online</H1>
    """


@functions_framework.http
def PracticeTurkishBotFunction(request: Request) -> Any:
    return app.dispatch(request)
