from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class Service(ABC):
    url: str

    @abstractmethod
    def process_data(self, data: dict[str, Any]) -> Any:
        raise NotImplementedError

    def post(self, /, *, path: str, data: dict[str, Any]) -> Any:
        return requests.post(
            url=f"{self.url}{path}", data=self.process_data(data)
        ).json()

    @classmethod
    @abstractmethod
    def from_config(cls, path: str = "config.ini") -> "Service":
        raise NotImplementedError
