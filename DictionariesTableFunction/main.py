from typing import Any
import json
import functions_framework  # type: ignore
from flask import Request, Response
from router import RequestRouter
from database import DictionariesTable

app = RequestRouter()
dictionaries_table = DictionariesTable.from_config()


@app.route("/post", "POST", to_json=True)
def insert_dictionary(data: dict[str, Any]) -> str:
    dictionary = data["dictionary"]
    return dictionaries_table.insert_dictionary(dictionary)
     
@app.route("/get", "POST", to_json=True)
def get_dictionary(data: dict[str, Any]) -> str:
    index = data["index"]
    return dictionaries_table.get_dictionary(index)

@app.route("/", "GET")
def status(_: dict[str, Any]) -> str:
    return """<title>UserTableFunction</title>
    <H1>The function is online</H1>
    """


@functions_framework.http
def DictionariesTableFunction(request: Request) -> Response:
    if request.method == "OPTIONS":
        response = Response("")
        response.status_code = 204
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        })
        return response
    return app.dispatch(request)
