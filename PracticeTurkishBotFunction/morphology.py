from configparser import ConfigParser

from httpx import AsyncClient  # type: ignore
from telegram import InlineKeyboardMarkup, InlineKeyboardButton  # type: ignore

from service import Service
from languages import Language, detect_language


class Morphology(Service):
    async def analyze(self, client: AsyncClient, /, *, word: str) -> str:
        return await self.async_post(client, path="/analyze", data={"word": word})

    async def is_available(self, client: AsyncClient, /, *, text: str) -> bool:
        if detect_language(text) != Language.turkish:
            return False
        if "." in text:
            return False
        if "," in text:
            return False
        if len(text.split()) != 1:
            return False
        return await self.async_post(client, path="/check", data={"word": text})

    @staticmethod
    def keyboard(word: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Morphology", callback_data=word)]]
        )

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "Morphology":
        config = ConfigParser()
        config.read(path)
        section = config["MORPHOLOGY FUNCTION"]
        return cls(section["URL"])
