from asyncio import run
from configparser import ConfigParser
import json
from io import StringIO
from time import sleep
from typing import Optional

from telegram import Bot, User, Update
from telegram.constants import ParseMode


def bot_from_config(path: str = "config.ini") -> Bot:
    "Reads a token from the config and returns an instance of Bot with the token"
    config = ConfigParser()
    config.read('config.ini')
    token = ":".join((config["BOT"]["id"], config["BOT"]["token"]))
    return get_bot(token)

def parse_message(update_data: bytes, bot: Bot) -> tuple[Optional[User], Optional[str], list[str]]:
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

    if update is None or update.message is None:
        print("No message")
        return None, None, [] 

    message = update.message
    if message.from_user is None:
        print("No user?")
        return None, None, []
   
    user = message.from_user    
    if user.id == bot.id:
        print("Message from me")
        return None, None, []

    if message.text is None:
        print("No text")
        return None, None, []

    text = message.text
    commands = [
        text[e.offset : e.offset + e.length] for e in message.entities
    ]
    for command in commands:
        text = text.replace(command, "")
    text = text.strip()
    text = " ".join(text.split())

    return user, text, commands 

def get_bot(token: str) -> Bot:
    "Synchronous version of _get_bot."
    return run(_get_bot(token))

def send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: ParseMode|None = None
    ) -> str:
    "Synchronous version of _send_text."
    s = run(_send_text(bot, chat_id, text, parse_mode))
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
    parse_mode: ParseMode|None = None
) -> str:
    """
    Sends text to a user via the bot.
    If the text is too big to be sent in a one message,
    it is splitted and several messages are sent.
    """
    async with bot:
        for chunk in split_into_chunks(text):
            await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
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
            
