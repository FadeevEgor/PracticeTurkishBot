from dataclasses import dataclass
import string
import secrets 
from typing import Optional, ClassVar
from configparser import ConfigParser

from pymongo import MongoClient
from pymongo.collection import Collection


@dataclass
class UsersTable:
    url: str
    tls_certificate_key_file: str
    database_name: str
    collection_name: str

    URL_template : ClassVar[string.Template] = string.Template(
        "${URL}?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
    ) 
    
    def get_collection(self) -> Collection:
        client = MongoClient(
            self.url, 
            tls=True,
            tlsCertificateKeyFile=self.tls_certificate_key_file 
        )
        database = client[self.database_name]
        return database[self.collection_name]      

    def lookup_token(self, user_id: int) -> Optional[str]:
        collection = self.get_collection()
        result = list(collection.find({"user_id": user_id}))
        if not result:
            return None
        return result[0]["token"]

    def insert_one(self, user_id: int, token: str) -> str:
        collection = self.get_collection()
        collection.insert_one({
            "user_id": user_id,
            "token": token
        })
        return token

    @classmethod
    def from_config(cls, path: str = "config.ini"):
        config = ConfigParser()
        config.read(path)
        db_info = config["DATABASE"]
        URL = cls.URL_template.substitute({"URL": db_info["Base URL"]})
        print(URL)
        return cls(
            URL,
            db_info['Certificate path'],
            db_info['Database name'],
            db_info['Collection name']
        )


def generate_token() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))


def get_token(table: UsersTable, user_id: int) -> str:
    token = table.lookup_token(user_id)
    if token is None:
        token = table.insert_one(user_id, generate_token())
    return token


if __name__ == "__main__":
    table = UsersTable.from_config()
    print(table.lookup_token(321))