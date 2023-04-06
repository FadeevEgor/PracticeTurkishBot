import functions_framework  # type: ignore
from flask import Request
from morphology import Morphology
from router import RequestRouter


app = RequestRouter()
morphology = Morphology()


@app.route("/check", "POST")
def check_if_interesting(data: dict) -> bool:
    word = data["word"]
    return morphology.check_if_interesting(word)


@app.route("/analyze", "POST")
def analyze(data: dict) -> str:
    word = data["word"]
    return morphology.analyze(word)


@app.route("/", "GET")
def status(data: dict) -> str:
    return """<title>MorphologyFunction</title>
    <H1>The function is online.</H1>"""


@functions_framework.http
def MorphologyFunction(request: Request) -> str:
    return app.dispatch(request)
