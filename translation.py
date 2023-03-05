import asyncio
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from string import ascii_lowercase
from typing import Optional

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from google.cloud import translate_v2 as translate


DEMEK_URL = "https://demek.ru/soz/?q={}"
GLOSBE_URL = "https://glosbe.com/{}/{}/{}"

PUNCTUATION_SYMBOLS = set(" ,.")
ENGLISH_SYMBOLS = set(ascii_lowercase) | PUNCTUATION_SYMBOLS
TURKISH_SYMBOLS = (set(ascii_lowercase) | set("âçğıiöşü") | PUNCTUATION_SYMBOLS) - set("qwx")
RUSSIAN_SYMBOLS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя") | PUNCTUATION_SYMBOLS



class Language(str, Enum):
    russian = "ru"
    turkish = "tk"
    english = "en"


def detect_language(text: str) -> Optional[Language]:
    symbols = set(text.lower())
    if symbols < TURKISH_SYMBOLS:
        return Language.turkish
    if symbols < RUSSIAN_SYMBOLS:
        return Language.russian
    if symbols < ENGLISH_SYMBOLS:
        return Language.english
    return None


@dataclass
class Translation:
    language: Optional[Language] = None
    demek: Optional[str] = None
    glosbe: Optional[str] = None
    google: Optional[str] = None


@dataclass
class Translator:
    google_client: translate.Client
    user_agent: UserAgent = UserAgent(browsers=["chrome", "edge", "firefox", "safari", "opera"])
    timeout: int = 3

    def translate(self, text: str) -> tuple[Optional[Language], Translation, Translation]:
        src_language = detect_language(text)
        if src_language is None:
            return (None, Translation(), Translation())
        tr1, tr2 = asyncio.run(self._translate(text, src_language))
        return (src_language, tr1, tr2)

    async def _translate(self, text: str, src: Language) -> tuple[Translation, Translation]:
        match src:
            case Language.turkish:
                ru_demek, ru_glosbe, en_glosbe, ru_google, en_google = await asyncio.gather(
                    self.demek(text),
                    self.glosbe(text, src, Language.russian),
                    self.glosbe(text, src, Language.english),
                    self.google(text, src, Language.russian),
                    self.google(text, src, Language.english)
                )
                ru = Translation(Language.russian, ru_demek, ru_glosbe, ru_google)
                en = Translation(Language.english, None, en_glosbe, en_google)
                return ru, en
            case Language.russian:
                tk_demek, tk_glosbe, en_glosbe, tk_google, en_google = await asyncio.gather(
                    self.demek(text),
                    self.glosbe(text, src, Language.turkish),
                    self.glosbe(text, src, Language.english),
                    self.google(text, src, Language.turkish),
                    self.google(text, src, Language.english)
                )
                tk = Translation(Language.turkish, tk_demek, tk_glosbe, tk_google)
                en = Translation(Language.english, None, en_glosbe, en_google)
                return tk, en
            case Language.english:
                ru_glosbe, tk_glosbe, ru_google, tk_google = await asyncio.gather(
                    self.glosbe(text, src, Language.russian),
                    self.glosbe(text, src, Language.turkish),
                    self.google(text, src, Language.russian),
                    self.google(text, src, Language.turkish)
                )
                ru = Translation(Language.russian, None, ru_glosbe, ru_google)
                tk = Translation(Language.turkish, None, tk_glosbe, tk_google)
                return ru, tk
 

    async def demek(self, text: str) -> Optional[str]:
        query = "+".join(text.split())
        url=DEMEK_URL.format(query)
        try: 
            response = self.request_get(url)
        except (requests.TooManyRedirects, requests.HTTPError, requests.Timeout) as msg:
            print(msg)
            return None
        
        print(f"demek: {query} - {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        search_result = soup.find("div", "item_bsc")
        if search_result is None:
            return None 
        return search_result.get_text()

    async def google(
            self, 
            text: str, 
            src: Language = Language.turkish, 
            dst: Language = Language.russian
        ) -> str:
        result = self.google_client.translate(
            values=text,
            source_language=src, 
            target_language=dst
        )
        return result["translatedText"]

    async def glosbe(
            self, 
            text: str, 
            src: Language = Language.turkish, 
            dst: Language = Language.russian
        ) -> Optional[str]:
        query = "%20".join(text.split())
            
        url = GLOSBE_URL.format(
            src if src != Language.turkish else "tr", 
            dst if dst != Language.turkish else "tr", 
            query
        )
        try:
            response = self.request_get(url)
        except (requests.TooManyRedirects, requests.HTTPError, requests.Timeout) as msg:
            print(msg)
            return None
        
        print(f"glosby: {query} - {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        summary_section = soup.find("p", attrs={"id": "content-summary"})
        bold_text = summary_section.find("strong")
        if bold_text is None:
            return None 
        return bold_text.get_text()
    
    @classmethod
    def from_config(cls, path: str = "config.ini") -> "Translator":
        config = ConfigParser()
        config.read(path)
        gcloud_key_path = config["GOOLGE FUNCTION"]["Key path"]
        return cls(
            translate.Client.from_service_account_json(gcloud_key_path),
        )

    def request_get(self, url: str) -> requests.Response:
        return requests.get(
            url=url,
            headers=self.request_header,
            timeout=self.timeout
        ) 

    @property
    def request_header(self) -> dict[str, str]:
        return {"User-Agent": str(self.user_agent.random)}
