from asyncio import run
from configparser import ConfigParser
from dataclasses import dataclass
import json
from io import StringIO
from time import sleep
from typing import Optional

import requests
from telegram import Bot, User, Update, Message
from telegram import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode


@dataclass
class UpdateContent:
    user: User
    text: str

@dataclass
class MessageContent(UpdateContent):
    commands: list[str]

@dataclass
class CallbackQueryContent(UpdateContent):
    pass

def bot_from_config(path: str = "config.ini") -> Bot:
    "Reads a token from the config and returns an instance of Bot with the token"
    config = ConfigParser()
    config.read('config.ini')
    token = ":".join((config["BOT"]["id"], config["BOT"]["token"]))
    return get_bot(token)

def parse_callback_query(query: CallbackQuery, bot: Bot) -> Optional[CallbackQueryContent]:
    print("Answering.")
    answer_callback_query(bot, query.id)
    print("Answered.")
    if query.data is None:
        print("Ignore: Query without data?")
        return None
    text = query.data
    user = query.from_user
    print(text)
    

    print("Removing keyboard.")
    remove_keyboard(bot, user.id, query.message.message_id)
    print("Removed keyboard.")
    return CallbackQueryContent(
        user,
        text 
    )

def parse_message(message: Message, bot: Bot) -> Optional[MessageContent]:
    if message.from_user is None:
        print("Ignore: No user?")
        return None
   
    user = message.from_user    
    if user.id == bot.id:
        print("Ignore: Message from me?")
        return None

    if message.text is None:
        print("Ignore: No text.")
        return None

    text = message.text
    commands = [
        text[e.offset : e.offset + e.length] for e in message.entities
    ]
    for command in commands:
        text = text.replace(command, "")
    text = text.strip()
    text = " ".join(text.split())
    return MessageContent(
        user,
        text,
        commands
    )

def parse_update(update_data: bytes, bot: Bot) -> Optional[UpdateContent]:
    """
    Parses content of a message from telegram.
    Returns a sender user, cleared from commands text and list of commands. 
    """
    data = json.loads(update_data)
    print(data)
    update = Update.de_json(
        data,
        bot
    )

    if update is None:
        print("No update")
        return None

    if update.message is not None:
        return parse_message(update.message, bot)
    
    if update.callback_query is not None:
        return parse_callback_query(update.callback_query, bot)
    return None

def get_bot(token: str) -> Bot:
    "Synchronous version of _get_bot."
    return run(_get_bot(token))

def send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: ParseMode|None = None,
    reply_markup: InlineKeyboardMarkup|None = None
    ) -> str:
    "Synchronous version of _send_text."
    s = run(_send_text(bot, chat_id, text, parse_mode, reply_markup))
    sleep(0.1)
    return s
 
async def _get_bot(token: str) -> Bot:
    "Creates a Bot instance with the token and checks its validity"
    bot = Bot(token)
    async with bot:
        user = await bot.get_me()
        print(user.username)
    return bot

async def _send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: ParseMode|None = None,
    reply_markup: InlineKeyboardMarkup|None = None
) -> str:
    """
    Sends text to a user via the bot.
    If the text is too big to be sent in a one message,
    it is splitted and several messages are sent.
    """
    chunks = split_into_chunks(text)
    n = len(chunks)
    async with bot:
        for i, chunk in enumerate(chunks, start=1):
            await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup if i == n else None 
                )
    return "Message sent"
            
def split_into_chunks(text: str, max_length: int = 4096) -> list[str]:
    "Splits text in chunks of length < 4096."
    rows = text.split("\n")
    
    current_chunk = StringIO()
    chunks : list[str] = []
    current_length = 0
    
    for row in rows:
        row_length = len(row)
        if current_length + row_length < max_length:
            current_chunk.write(row)
            current_length += row_length
        else:
            chunks.append(current_chunk.getvalue())
            current_chunk = StringIO()
            current_length = 0
    chunks.append("".join(current_chunk))
    return chunks


def answer_callback_query(bot: Bot, query_id: str) -> int:
    token = bot.token
    method = "answerCallbackQuery"
    data = {"callback_query_id": query_id, "text": "Processing..."}
    return requests.post(
        f"https://api.telegram.org/bot{bot.token}/{method}",
        data=data
    ).status_code

def remove_keyboard(bot: Bot, chat_id: int, message_id: int) -> int:
    method = "editMessageReplyMarkup"
    data = {"chat_id": chat_id, "message_id": message_id}
    return requests.post(
        f"https://api.telegram.org/bot{bot.token}/{method}",
        data=data
    ).status_code

def morphology_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Morphology", callback_data=word)
    ]])
