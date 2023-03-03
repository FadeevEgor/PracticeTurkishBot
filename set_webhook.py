from configparser import ConfigParser
import requests

config = ConfigParser()
config.read("config.ini")

BOT_Section = config["BOT"]
FUNCTION_section = config["GOOGLE FUNCTION"]

token = ":".join((BOT_Section["Id"], BOT_Section["Token"]))
webhook_URL = f"{FUNCTION_section['Base URL']}/webhook"
bot_URL = f"https://api.telegram.org/bot{token}/setWebhook"

response = requests.post(
    url=bot_URL,
    data={
        "url": webhook_URL
    }
)
print(response.status_code, response.text)