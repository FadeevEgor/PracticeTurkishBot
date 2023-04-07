from configparser import ConfigParser
from typing import Any, Dict, List
from time import sleep
from service import Service


class TelegramBot(Service):
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def send_text(
        self,
        chat_id: int,
        text: str,
    ) -> Any:
        return self.sync_post(
            path="sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )

    def send_out(
        self,
        chat_ids: List[int],
        text: str,
        pause: int,
    ) -> Any:
        for id in chat_ids:
            response = self.send_text(id, text)
            sleep(pause)
        return response

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "TelegramBot":
        config = ConfigParser()
        config.read(path)
        BOT_SECTION = config["BOT"]
        bot_id = BOT_SECTION["id"]
        bot_secret = BOT_SECTION["secret"]
        token = f"{bot_id}:{bot_secret}"
        return cls(f"https://api.telegram.org/bot{token}/")
