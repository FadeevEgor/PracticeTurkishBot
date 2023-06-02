from typing import Any
from functools import partial
from flask import Request, Response, abort
import functions_framework  # type: ignore
from database import UserTable, DictionaryTable
from router import RequestRouter
from telegram import TelegramBot, ParseMode


app = RequestRouter()
bot = TelegramBot.from_config()
user_table = UserTable.from_config()
dictionary_table = DictionaryTable.from_config()


app_url = "http://t.me/PracticeTurkishBot/quiz"


def send_to_telegram(user_id: int, text: str) -> None:
    print(text)
    index = dictionary_table.register_dictionary(text)
    text += f'\n\n<a href="{app_url}?startapp={index}"><b>Practice!</b></a>'
    bot.send_text(user_id, text, ParseMode.HTML)


@app.route("/", "POST")
def redirect(data: dict[str, Any]) -> Response:
    user_id = data["user id"]
    token = data["token"]
    if not user_table.check_token(user_id, token):
        return abort(403)

    text = data["text"]
    response = Response("Message successfully sent!", 200)
    response.call_on_close(partial(send_to_telegram, user_id, text))
    return response


@app.route("/", "GET")
def status(_: dict[str, Any]) -> Response:
    return Response(
        """<title>PracticeTurkishBot</title>
    <H1>The bot is online</H1>
    """,
        200,
    )


@functions_framework.http
def RedirectFunction(request: Request) -> Response:
    return app.dispatch(request)
