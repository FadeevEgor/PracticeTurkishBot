from httpx import AsyncClient  # type: ignore
from telegram import Bot, Message  # type: ignore
from telegram.constants import ParseMode  # type: ignore

from translation import Translator
from bot.actions import send_text_async


async def translate_and_send(
    translator: Translator, client: AsyncClient, text: str, bot: Bot, chat_id: int
) -> Message:
    report = await translator.translate(client, text=text)
    return await send_text_async(bot, chat_id, report.translation, ParseMode.HTML)
