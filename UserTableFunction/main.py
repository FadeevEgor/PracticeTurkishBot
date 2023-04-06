from typing import Any
import functions_framework  # type: ignore
from flask import Request
from router import RequestRouter
from database import UserTable

app = RequestRouter()
user_table = UserTable.from_config()


@app.route("/get_token", "POST")
def get_token(data: dict[str, Any]) -> str:
    key = data["key"]
    user_id = data["user_id"]
    return user_table.new_user(key, user_id)


@app.route("/check_token", "POST")
def check_token(data: dict[str, Any]) -> bool:
    key = data["key"]
    user_id = data["user_id"]
    token = data["token"]
    return user_table.check_user_token(key, user_id, token)


@app.route("/subscribers", "POST")
def subscribers(data: dict[str, Any]) -> list[int]:
    key = data["key"]
    return user_table.get_list_of_subscribers(key)


@app.route("/subscribe", "POST")
def subscribe(data: dict[str, Any]) -> bool:
    key = data["key"]
    user_id = data["user_id"]
    return user_table.subscribe(key, user_id)


@app.route("/unsubscribe", "POST")
def unsubscribe(data: dict[str, Any]) -> bool:
    key = data["key"]
    user_id = data["user_id"]
    return user_table.unsubscribe(key, user_id)


@app.route("/", "GET")
def status(_: dict[str, Any]) -> str:
    return """<title>UserTableFunction</title>
    <H1>The function is online</H1>
    """


@functions_framework.http
def UserTableFunction(request: Request) -> Any:
    return app.dispatch(request)
