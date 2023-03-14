from abc import ABC, abstractmethod
import asyncio
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Optional, Type, ClassVar

from bs4 import BeautifulSoup
from google.cloud import translate_v2 as translate

from requestor import Requestor
from languages import Language, ISO_639_codes, detect_language 


@dataclass
class Translation:
    text: str
    service: str


@dataclass
class TranslationsToTheSameLanguage:
    language: Language
    translations: list[Translation]


class TranslationService(ABC):
    """
    ABC for translation service.
    Each service should implement following methods:
        - translate;
        - representing_url;
        - supported_languages (if not all language combinations are supported).

    If the service uses an encoding different to ISO-639-1, the method language_encodings 
    should be overridden.
    """

    @abstractmethod
    async def translate(
        self, 
        text: str, 
        src_language_code: str, 
        dst_language_code: str,
        requestor: Requestor
    ) -> Optional[str]:
        """
        Takes text to be translated, its language and target language.
        Returns translated text or None error is encountered or unsupported languages are specified. 
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def representing_url(self) -> str:
        """
        Returns a URL representing service.
        """
        raise NotImplementedError
    
    @property
    def language_encoding(self) -> dict[Language, str]:
        """
        A mapping from a language to its code used by the service.
        An empty dictionary corresponds to ISO-639-1.
        All languages whose codes differ from ISO-639 standard should be listened here.
        """
        return {}

    @property
    def supported_languages(self) -> set[tuple[Language, Language]]:
        """
        A set of supported combinations of languages.
        Each element is a tuple (l1, l2) of two Language instances.
        Translation from l1 to l2 is supported iff tuple (l1, l2) is present in the set.
        Should be overridden if not all combinations of languages are supported.
        """
        return {
            (Language.russian, Language.turkish),
            (Language.turkish, Language.russian),
            (Language.russian, Language.english),
            (Language.english, Language.russian),
            (Language.turkish, Language.english),
            (Language.english, Language.turkish),
        }
     
    async def _translate(
        self, 
        text: str, 
        src: Language, 
        dst: Language,
        requestor: Requestor
    ) -> Optional[Translation]:
        """
        Wraps method translate.
        - checks if the language combination is supported;
        - encodes languages via encode_language method;
        - calls translate method and wraps result in a Translation object.
        """
        if (src, dst) not in self.supported_languages:
            return None
        src_language_code = self._encode_language(src)
        dst_language_code = self._encode_language(dst)
        translated_text = await self.translate(
            text,
            src_language_code,
            dst_language_code,
            requestor
        )
        if translated_text is None:
            return None    
        return Translation(translated_text, self.representing_url)

    def _encode_language(self, language: Language) -> str:
        """
        Uses language_encoding property to encode a language.
        Falls back to ISO-639-1 if the language is absent in language_encoding.
        """
        return self.language_encoding.get(language, ISO_639_codes[language])


@dataclass
class Translator:
    """
    The main class for translating. 
    Aggregates all translation services via register_service decorator,
    calls each of them and returns aggregated results to the caller. 
    """
    requestor: Requestor = Requestor()
    services: ClassVar[list[TranslationService]] = []

    @classmethod
    def register_service(cls, service_type: Type[TranslationService]) -> Type[TranslationService]:
        "Decorator for service registration."
        service = service_type()
        cls.services.append(service)
        return service_type

    def translate(
            self, 
            text: str
        ) -> tuple[
            Optional[Language], 
            Optional[tuple[TranslationsToTheSameLanguage, TranslationsToTheSameLanguage]]
        ]:
        """
        Detects the language of the text and returns aggregated results of translation 
        to all supported languages via all registered services. 
        """
        src = detect_language(text)
        if src is None:
            return (None, None)
        dst_1, dst_2 = [x for x in Language if x != src]
        return (
            src, 
            (
                self.translate_to_the_language(text, src, dst_1), 
                self.translate_to_the_language(text, src, dst_2),
            ) 
        )

    def translate_to_the_language(
            self, 
            text: str, 
            src: Language, 
            dst: Language
        ) -> TranslationsToTheSameLanguage:    
        translations = asyncio.run(self._translate_to_the_language(text, src, dst))
        translations = [t for t in translations if t is not None]
        return TranslationsToTheSameLanguage(
            dst,
            translations
        )
    
    async def _translate_to_the_language(
            self, 
            text: str, 
            src: Language, 
            dst: Language
        ) -> list[Optional[Translation]]:    
        to_gather = []
        for service in self.services:
            to_gather.append(service._translate(text, src, dst, self.requestor))
        return await asyncio.gather(*to_gather)
    



@Translator.register_service
class DemekRu(TranslationService):
    URL = "https://demek.ru/soz/?q={}"

    @property
    def representing_url(self) -> str:
        return "demek.ru"

    @property
    def supported_languages(self) -> set[tuple[Language, Language]]:
        return {
            (Language.russian, Language.turkish),
            (Language.turkish, Language.russian),
        }
    
    async def translate(
        self, 
        text: str, 
        src_language_code: str, 
        dst_language_code: str,
        requestor: Requestor
    ) -> Optional[str]:
        query = "+".join(text.split())
        url = self.URL.format(query)
        response = requestor.get(url)
        if response is None:
            return None

        print(f"demek: {query} - {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        search_result = soup.find("div", "item_bsc")
        if search_result is None:
            return None 
        return search_result.get_text()

        

@Translator.register_service
class GlosbeCom(TranslationService):
    URL = "https://glosbe.com/{}/{}/{}"
    
    @property
    def representing_url(self) -> str:
        return "glosbe.com"

    async def translate(
        self, 
        text: str, 
        src_language_code: str, 
        dst_language_code: str,
        requestor: Requestor
    ) -> Optional[str]:
        query = "%20".join(text.split())   
        url = self.URL.format(
            src_language_code, 
            dst_language_code, 
            query
        )
        print(url)
        response = requestor.get(url)
        if response is None:
            return None

        print(f"glosby: {query} - {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        summary_section = soup.find("p", attrs={"id": "content-summary"})
        bold_text = summary_section.find("strong")
        if bold_text is None:
            return None 
        return bold_text.get_text()
            

@dataclass
class GoogleTranslateClient:
    client: translate.Client
    
    @classmethod
    def from_config(cls, path: str = "config.ini") -> "GoogleTranslateClient":
        config = ConfigParser()
        config.read(path)
        gcloud_key_path = config["GOOLGE FUNCTION"]["Key path"]
        return cls(
            translate.Client.from_service_account_json(gcloud_key_path),
        )

@Translator.register_service
class GoogleTranslate(TranslationService):
    def __init__(self) -> None:
        super().__init__()
        self.client = GoogleTranslateClient.from_config()
    
    @property
    def representing_url(self) -> str:
        return "google.com"

    async def translate(
        self, 
        text: str, 
        src_language_code: str, 
        dst_language_code: str,
        requestor: Requestor
    ) -> Optional[str]:
        response = self.client.client.translate(
            values=text,
            source_language=src_language_code, 
            target_language=dst_language_code
        )
        return response["translatedText"]
    

@Translator.register_service
class TurkcesozlukNet(TranslationService):
    URL = "https://www.turkcesozluk.net/index.php?word={}"
        
    @property
    def representing_url(self) -> str:
        return "turkcesozluk.net"
    
    async def translate(
        self, 
        text: str, 
        src_language_code: str, 
        dst_language_code: str,
        requestor: Requestor
    ) -> Optional[str]:
        query = "+".join(text.split())
        url = self.URL.format(query)
        
        response = requestor.get(url)
        if response is None:
            return None
        
        name_attr = src_language_code + dst_language_code
        print(name_attr)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"name": name_attr})
        if table is None:
            return None
        
        table_content = table.find_all("tr")[1]
        first_row = table_content.find("tr")
        cell = first_row.find_all("td")[1]
        list = cell.find("ul", {"class": "ulc"}) 
        if list is None:
            return cell.get_text()
        points = list.find_all("li")
        return " ".join(p.get_text() for p in points)    
         