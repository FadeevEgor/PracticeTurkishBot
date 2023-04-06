from httpx import AsyncClient  # type: ignore
from telegram import Bot, User, Message  # type: ignore
from telegram.constants import ParseMode  # type: ignore

from translation import Translator
from telegram_bot.api import send_text_async


async def translate_and_send(
    translator: Translator, client: AsyncClient, bot: Bot, user: User, text: str
) -> Message:
    report = await translator.translate(client, text=text)
    return await send_text_async(bot, user.id, report.translation, ParseMode.HTML)
