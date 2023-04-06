from typing import Any
import flask
import functions_framework  # type: ignore
from database import UserTable
from router import RequestRouter
from telegram import TelegramBot


app = RequestRouter()
bot = TelegramBot.from_config()
user_table = UserTable.from_config()


@app.route("/", "POST")
def redirect(data: dict[str, Any]) -> str:
    user_id = data["user id"]
    token = data["token"]
    if not user_table.check_token(user_id, token):
        return flask.abort(403)

    text = data["text"]
    bot.send_text(user_id, text)
    return "Message sent"


@app.route("/", "GET")
def status(_: dict[str, Any]) -> str:
    return """<title>PracticeTurkishBot</title>
    <H1>The bot is online</H1>
    """


@functions_framework.http
def RedirectFunction(request: flask.Request) -> Any:
    return app.dispatch(request)
