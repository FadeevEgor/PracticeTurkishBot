from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Any, TypeAlias

from httpx import AsyncClient, post  # type: ignore


_Data: TypeAlias = dict[str, Any]


@dataclass
class Service(ABC):
    url: str

    def process_data(self, data: _Data) -> str:
        return json.dumps(data)

    async def async_post(
        self, client: AsyncClient, /, *, path: str, data: _Data
    ) -> Any:
        response = await client.post(
            url=f"{self.url}{path}", data=self.process_data(data), timeout=10
        )
        return response.json()

    def post(self, /, *, path: str, data: _Data) -> Any:
        response = post(
            url=f"{self.url}{path}", data=self.process_data(data), timeout=10
        )
        return response.json()

    @classmethod
    @abstractmethod
    def from_config(cls, path: str = "config.ini") -> "Service":
        raise NotImplementedError
