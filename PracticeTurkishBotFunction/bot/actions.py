import asyncio
from configparser import ConfigParser
from io import StringIO

from telegram import Bot, Message  # type: ignore
from telegram import InlineKeyboardMarkup  # type: ignore
from telegram.constants import ParseMode  # type: ignore


def bot_from_config(path: str = "config.ini") -> Bot:
    "Reads a token from the config and returns an instance of Bot with the token"
    config = ConfigParser()
    config.read(path)
    id = config["BOT"]["id"]
    secret = config["BOT"]["secret"]
    token = f"{id}:{secret}"
    return get_bot(token)


def get_bot(token: str) -> Bot:
    "Synchronous version of _get_bot."
    return asyncio.run(_get_bot(token))


def send_text_sync(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: ParseMode | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    "Synchronous version of _send_text."
    return asyncio.run(send_text_async(bot, chat_id, text, parse_mode, reply_markup))


async def _get_bot(token: str) -> Bot:
    "Creates a Bot instance with the token and checks its validity"
    bot = Bot(token)
    async with bot:
        user = await bot.get_me()
        print(user.username)
    return bot


async def send_text_async(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: ParseMode | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    """
    Sends text to a user via the bot.
    If the text is too big to be sent in a one message,
    it is splitted and several messages are sent.
    """
    chunks = split_into_chunks(text)
    n = len(chunks)
    async with bot:
        for i, chunk in enumerate(chunks, start=1):
            message = await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                reply_markup=reply_markup if i == n else None,
            )
    return message


def split_into_chunks(text: str, max_length: int = 3500) -> list[str]:
    "Splits text in chunks of length < 4096."
    rows = text.split("\n")
    current_chunk = StringIO()
    chunks: list[str] = []
    current_length = 0

    for row in rows:
        row_length = len(row)
        if current_length + row_length < max_length:
            current_chunk.write(row + "\n")
            current_length += row_length
        else:
            chunks.append(current_chunk.getvalue().strip())
            current_chunk = StringIO()
            current_length = 0
    chunks.append(current_chunk.getvalue().strip())
    return [c for c in chunks if c]


async def answer_callback_query_and_remove_query(
    bot: Bot, query_id: str, chat_id: int, message_id: int
) -> None:
    async with bot:
        await asyncio.gather(
            bot.answer_callback_query(callback_query_id=query_id),
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id),
        )


async def edit_keyboard(
    bot: Bot, chat_id: int, message_id: int, keyboard: InlineKeyboardMarkup
) -> int:
    async with bot:
        return await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=keyboard
        )


async def send_action_typing(bot: Bot, chat_id: int) -> bool:
    async with bot:
        return await bot.send_chat_action(chat_id=chat_id, action="typing")
