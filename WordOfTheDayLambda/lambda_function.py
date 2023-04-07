import asyncio
import json
from typing import Any, Dict, Tuple, List
from httpx import AsyncClient  # type: ignore

from database import UserTable
from telegram import TelegramBot
from word_of_the_day import word_of_the_day


CONFIG_PATH = "/opt/config.ini"
bot = TelegramBot.from_config(CONFIG_PATH)
user_table = UserTable.from_config(CONFIG_PATH)


async def text_and_users() -> Tuple[str, List[int]]:
    async with AsyncClient() as client:
        return await asyncio.gather(
            word_of_the_day(client), user_table.list_of_subscribers(client)
        )


def lambda_handler(*_: Any, **__: Any) -> Dict[str, Any]:
    text, users = asyncio.run(text_and_users())
    print(text, users)
    print(bot.send_out(users, text, 1))
    return {"statusCode": 200, "body": json.dumps(text)}


def main() -> None:
    lambda_handler()


if __name__ == "__main__":
    main()
