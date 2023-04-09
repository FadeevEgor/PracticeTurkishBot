from configparser import ConfigParser
from httpx import post  # type: ignore
from bot.actions import bot_from_config


bot = bot_from_config()

config = ConfigParser()
config.read("config.ini")
BOT_FUNCTION_Section = config["BOT FUNCTION"]
FUNCTION_URL = BOT_FUNCTION_Section["URL"]
bot_URL = f"https://api.telegram.org/bot{bot.token}/setWebhook"

response = post(
    url=bot_URL,
    data={
        "url": FUNCTION_URL,
    },
)
print(response.status_code, response.text)
