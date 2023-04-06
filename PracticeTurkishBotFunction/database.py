from configparser import ConfigParser
from dataclasses import dataclass
from service import Service, _Data


@dataclass
class UserTable(Service):
    key: str

    def process_data(self, data: _Data) -> str:
        data["key"] = self.key
        return super().process_data(data)

    def subscribe(self, user_id: int) -> bool:
        return self.post(path="/subscribe", data={"user_id": user_id})

    def unsubscribe(self, user_id: int) -> bool:
        return self.post(path="/unsubscribe", data={"user_id": user_id})

    def get_token(self, user_id: int) -> bool:
        return self.post(path="/get_token", data={"user_id": user_id})

    def check_token(self, user_id: int, given_token: str) -> bool:
        return self.post(
            path="/check_token",
            data={
                "user_id": user_id,
                "token": given_token,
            },
        )

    def list_of_subscribers(self) -> list[int]:
        return self.post(path="/subscribers", data={})

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "UserTable":
        config = ConfigParser()
        config.read(path)
        section = config["USER TABLE FUNCTION"]
        return cls(section["URL"], section["KEY"])
