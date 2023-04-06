from configparser import ConfigParser
from dataclasses import dataclass
import hmac
import json
import secrets
import string
from time import perf_counter
from typing import ClassVar, Optional

import requests


class DBError(Exception):
    pass


class UserTableKeyError(DBError):
    pass


class NonExistingUserError(DBError):
    pass


@dataclass
class UserTable:
    key: str
    region: str
    service: str
    cluster: str
    database: str
    collection: str
    api_key: str
    _url_common: ClassVar[
        str
    ] = "data.mongodb-api.com/app/data-zvtvp/endpoint/data/v1/action"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Access-Control-Request-Headers": "*",
            "api-key": self.api_key,
        }

    @property
    def default_payload(self) -> dict[str, str]:
        return {
            "collection": self.collection,
            "database": self.database,
            "dataSource": self.cluster,
        }

    def authenticate(self, given_key: str) -> bool:
        return hmac.compare_digest(self.key, given_key)

    def url(self, method: str) -> str:
        return f"https://{self.region}.{self.service}.{self._url_common}/{method}"

    @staticmethod
    def get_projection(fields: list[str]) -> dict:
        projection = {"_id": False} | {field: True for field in fields}
        return projection

    def request(self, key: str, method: str, payload: dict) -> dict:
        if not self.authenticate(key):
            raise UserTableKeyError("Wrong key for UserTable!")
        payload |= self.default_payload
        return requests.post(
            url=self.url(method),
            headers=self.headers,
            data=json.dumps(payload),
        ).json()

    def get_list_of_subscribers(self, key: str) -> list[int]:
        payload = {
            "filter": {"wotd": True},
            "projection": self.get_projection(["user_id"]),
        }
        response = self.request(key, "find", payload)
        return [doc["user_id"] for doc in response["documents"]]

    def subscribe(self, key: str, user_id: int) -> bool:
        payload = {"filter": {"user_id": user_id}, "update": {"$set": {"wotd": True}}}
        response = self.request(key, "updateOne", payload)
        if response["modifiedCount"] == 0:
            raise NonExistingUserError(f"There is no user with id={user_id} in the DB.")
        return True

    def unsubscribe(self, key: str, user_id: int) -> bool:
        payload = {"filter": {"user_id": user_id}, "update": {"$set": {"wotd": False}}}
        response = self.request(key, "updateOne", payload)
        if response["modifiedCount"] == 0:
            raise NonExistingUserError(f"There is no user with id={user_id} in the DB.")
        return False

    def get_user_token(self, key: str, user_id: int) -> str:
        payload = {
            "filter": {"user_id": user_id},
            "projection": self.get_projection(["token"]),
        }
        response = self.request(key, "findOne", payload)
        document = response["document"]
        if document is None:
            raise NonExistingUserError(f"There is no user with id={user_id} in the DB.")
        return document["token"]

    def check_user_token(self, key: str, user_id: int, given_token: str) -> bool:
        true_token = self.get_user_token(key, user_id)
        return hmac.compare_digest(true_token, given_token)

    def new_user(self, key: str, user_id: int) -> str:
        try:
            token = self.get_user_token(key, user_id)
        except NonExistingUserError:
            token = generate_token()
            payload = {
                "document": {
                    "user_id": user_id,
                    "token": token,
                    "wotd": False,
                }
            }
            response = self.request(key, "insertOne", payload)
        return token

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "UserTable":
        config = ConfigParser()
        config.read(path)
        auth_section = config["AUTH"]
        mongoDB_section = config["MONGODB"]
        return cls(
            auth_section["key"],
            mongoDB_section["region"],
            mongoDB_section["service"],
            mongoDB_section["cluster"],
            mongoDB_section["database"],
            mongoDB_section["collection"],
            mongoDB_section["api-key"],
        )


def generate_token() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(8))
