from configparser import ConfigParser
from dataclasses import dataclass
import json
from typing import Any
from service import Service

from httpx import AsyncClient  # type: ignore


@dataclass
class UserTable(Service):
    key: str

    def process_data(self, data: dict[str, Any]) -> str:
        data["key"] = self.key
        return json.dumps(data)

    async def list_of_subscribers(self, client: AsyncClient) -> list[int]:
        return await self.async_post(client, path="/subscribers", data={})

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "UserTable":
        config = ConfigParser()
        config.read(path)
        section = config["USER TABLE FUNCTION"]
        return cls(section["url"], section["key"])
