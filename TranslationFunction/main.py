from dataclasses import asdict
import functions_framework  # type: ignore
from flask import Request

from translation import Translator, get_translation
from router import RequestRouter


translator = Translator()
app = RequestRouter()


@app.route("/", "POST")
def translate(data: dict) -> dict:
    text = data["text"]
    return asdict(get_translation(translator, text))


@app.route("/", "GET")
def status(data: dict) -> str:
    return """<title>TranslationFunction</title>
    <H1>The function is online.</H1>"""


@functions_framework.http
def TranslationFunction(request: Request) -> str:
    return app.dispatch(request)
