from configparser import ConfigParser
from enum import Enum
from typing import Optional, Any
from service import Service


class ParseMode(str, Enum):
    HTML = "HTML"
    MARKDOWN = "Markdown"
    MARKDOWN_V2 = "MarkdownV2"


class TelegramBot(Service):
    def process_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def send_text(
        self, chat_id: int, text: str, parse_mode: Optional[ParseMode] = None
    ) -> dict[str, Any]:
        return self.post(
            path="sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
        )

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "TelegramBot":
        config = ConfigParser()
        config.read(path)
        BOT_SECTION = config["BOT"]
        bot_id = BOT_SECTION["id"]
        bot_secret = BOT_SECTION["secret"]
        token = f"{bot_id}:{bot_secret}"
        return cls(f"https://api.telegram.org/bot{token}/")
