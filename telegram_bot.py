import json
from configparser import ConfigParser
from asyncio import run
from time import sleep
from typing import Optional

from telegram import Bot, User, Update
from telegram.constants import ParseMode


def bot_from_config(path: str = "config.ini") -> Bot:
    config = ConfigParser()
    config.read('config.ini')
    token = ":".join((config["BOT"]["id"], config["BOT"]["token"]))
    return get_bot(token)

def parse_command(update_data: bytes, bot: Bot) -> tuple[Optional[User], list[str]]:
    data = json.loads(update_data)
    print(data)
    update = Update.de_json(
        data,
        bot
    )

    if update is None or update.message is None:
        print("No message")
        return None, []

    message = update.message
    if message.from_user is None:
        print("No user?")
        return None, []
   
    user = message.from_user    
    if user.id == bot.id:
        print("Message from me")
        return None, []

    if message.text is None:
        print("No text")
        return None, []

    text = message.text
    commands = [
        text[e.offset : e.offset + e.length] for e in message.entities
    ]  
    return user, commands 

def get_bot(token: str) -> Bot:
    return run(_get_bot(token))

def send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    markdown: bool = False,
    ) -> str:
    s = run(_send_text(bot, chat_id, text, markdown))
    sleep(0.1)
    return s
 
async def _get_bot(token: str) -> Bot:
    bot = Bot(token)
    async with bot:
        user = await bot.get_me()
        print(user.username)
    return bot

async def _send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    markdown: bool = False
) -> str:
    async with bot:
        for chunk in split_into_chunks(text):
            await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN_V2 if markdown else None
                )
    return "Message sent"
            
def split_into_chunks(text: str, max_length: int = 4096) -> list[str]:
    rows = text.split("\n")
    
    current_chunk : list[str] = []
    chunks : list[str] = []
    current_length = 0
    
    for row in rows:
        row_length = len(row)
        if current_length + row_length < max_length:
            current_chunk.append(row)
            current_length += row_length
        else:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_length = 0
    chunks.append("".join(current_chunk))
    return chunks
            
