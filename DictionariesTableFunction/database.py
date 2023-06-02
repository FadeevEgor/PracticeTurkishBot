from configparser import ConfigParser
from dataclasses import dataclass
from typing import TypeAlias
import json
from typing import ClassVar

import requests

Dictionary : TypeAlias = list[tuple[str, str]]


class DBError(Exception):
    pass


class UserTableKeyError(DBError):
    pass


class NonExistingUserError(DBError):
    pass


@dataclass
class DictionariesTable:
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

    
    def url(self, method: str) -> str:
        return f"https://{self.region}.{self.service}.{self._url_common}/{method}"

    @staticmethod
    def get_projection(fields: list[str]) -> dict:
        projection = {"_id": False} | {field: True for field in fields}
        return projection

    def request(self, method: str, payload: dict) -> dict:
        payload |= self.default_payload
        return requests.post(
            url=self.url(method),
            headers=self.headers,
            data=json.dumps(payload),
        ).json()
    
    def get_dictionary(self, index: int) -> Dictionary:
        payload = {
            "filter": {"index": index},
            "projection": self.get_projection(["dictionary"]),
        }
        response = self.request("findOne", payload)
        document = response["document"]
        if document is None:
            return []
        return document["dictionary"]

    def get_index(self, inserted_id: str) -> int:
        payload = {
            "filter": {"_id": {"$oid": inserted_id}},
            "projection": self.get_projection(["index"])
        }
        while True:
            response = self.request("findOne", payload)
            document = response["document"]
            index = document.get("index", 0)
            if index:
                return index

    def insert_dictionary(self, dictionary: Dictionary) -> int:
        payload = {
            "document": {
                "dictionary": dictionary,
            }
        }
        response = self.request("insertOne", payload)
        inserted_id = response["insertedId"]
        return self.get_index(inserted_id)

    
    @classmethod
    def from_config(cls, path: str = "config.ini") -> "DictionariesTable":
        config = ConfigParser()
        config.read(path)
        mongoDB_section = config["MONGODB"]
        return cls(
            mongoDB_section["region"],
            mongoDB_section["service"],
            mongoDB_section["cluster"],
            mongoDB_section["database"],
            mongoDB_section["collection"],
            mongoDB_section["api-key"],
        )

