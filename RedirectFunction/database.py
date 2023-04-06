from configparser import ConfigParser
from dataclasses import dataclass
import json
from typing import Any
from service import Service


@dataclass
class UserTable(Service):
    key: str

    def process_data(self, data: dict[str, Any]) -> str:
        data["key"] = self.key
        return json.dumps(data)

    def check_token(self, user_id: int, given_token: str) -> bool:
        return self.post(
            path="/check_token",
            data={
                "user_id": user_id,
                "token": given_token,
            },
        )

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "UserTable":
        config = ConfigParser()
        config.read(path)
        section = config["USER TABLE FUNCTION"]
        return cls(section["url"], section["key"])
