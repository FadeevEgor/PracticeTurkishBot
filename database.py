from configparser import ConfigParser
from dataclasses import dataclass
import hmac
import secrets 
import string
from typing import Optional, ClassVar

from pymongo import MongoClient
from pymongo.collection import Collection


def generate_token() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))


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

    def new_user(self, user_id: int, token: str) -> None:
        collection = self.get_collection()
        collection.insert_one({
            "user_id": user_id,
            "token": token,
            "wotd": False,
        })
    
    def lookup_token(self, user_id: int) -> Optional[str]:
        collection = self.get_collection()
        result = collection.find_one({"user_id": user_id})
        if not result:
            return None
        return result["token"]

    def get_token(self, user_id: int) -> str:
        token = self.lookup_token(user_id)
        if token is None:
            token = generate_token()
            self.new_user(user_id, token)
        return token    

    def check_token(self, user_id: int, given_token: str) -> bool:
        true_token = self.get_token(user_id)
        return hmac.compare_digest(true_token, given_token)


    def subscribe(self, user_id) -> None:
        collection = self.get_collection()
        collection.find_one_and_update(
            filter={"user_id": user_id}, 
            update={"$set": {
            "wotd": True
            }
        })

    def unsubscribe(self, user_id) -> None:
        collection = self.get_collection()
        collection.find_one_and_update(
            filter={"user_id": user_id}, 
            update={"$set": {
            "wotd": False
            }
        })

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
