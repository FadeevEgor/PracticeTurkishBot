from configparser import ConfigParser
from dataclasses import dataclass
from typing import Optional

from languages import Language
from service import Service
from httpx import AsyncClient  # type: ignore


@dataclass
class Translation:
    text: str
    language: Optional[Language]
    translation: str


class Translator(Service):
    async def translate(self, client: AsyncClient, /, *, text: str) -> Translation:
        data = await self.async_post(client, path="/", data={"text": text})
        language = data["language"]
        return Translation(
            data["text"],
            Language[language] if language is not None else None,
            data["translation"],
        )

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "Translator":
        config = ConfigParser()
        config.read(path)
        section = config["TRANSLATION FUNCTION"]
        return cls(url=section["url"])
