from abc import ABC, abstractmethod
import asyncio
from configparser import ConfigParser
from dataclasses import dataclass
from io import StringIO
from typing import Optional, Type, ClassVar

from aiohttp import ClientSession, ClientSSLError  # type: ignore
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from google.cloud import translate_v2 as translate  # type: ignore
from emoji import emojize  # type: ignore
from fake_useragent import UserAgent  # type: ignore

from languages import (
    Language,
    ISO_639_codes,
    detect_language,
    lang_to_flag,
    genitive_cases,
)


async def make_request(
    url: str, session: ClientSession, timeout: int = 3
) -> str | None:
    try:
        async with session.get(url=url, timeout=timeout) as r:
            return await r.text()
    except (ClientSSLError, asyncio.TimeoutError) as e:
        print(e)
        return None


@dataclass(slots=True)
class Translation:
    text: str
    translation: str
    language: Optional[Language] = None


@dataclass(slots=True)
class TranslationUnit:
    text: str
    service_name: str
    url: str


@dataclass(slots=True)
class TranslationsToTheSameLanguage:
    src: Language
    translations: list[TranslationUnit]


@dataclass(slots=True)
class TranslationsToBothLanguages:
    src: Language
    dst_1: TranslationsToTheSameLanguage
    dst_2: TranslationsToTheSameLanguage


def get_translation(translator: "Translator", text: str) -> Translation:
    """
    Given text of a message by an user, generates a content for a response message
    based on results by the translator instance.
    """
    translations = translator.translate(text)
    if translations is None:
        awkward_emoji = emojize(":downcast_face_with_sweat:")
        return Translation(text, f"Не смог распознать язык {awkward_emoji}.")

    src = translations.src
    src_flag = lang_to_flag[src]
    src_gen = genitive_cases[src]
    result = StringIO()
    result.write(
        f'Перевод для "<b>{text}</b>" с {src_flag}<b>{src_gen}</b>{src_flag} языка.\n\n'
    )
    for dst in (translations.dst_1, translations.dst_2):
        dst_flag = lang_to_flag[dst.src]
        result.write(f"{src_flag} ➔ {dst_flag}:\n")
        for t in dst.translations:
            result.write(f'<a href="{t.url}"><b>{t.service_name}</b></a>: {t.text}.\n')
        result.write("\n")
    return Translation(text=text, translation=result.getvalue(), language=src)


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
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def service_name(self) -> str:
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

    async def wrap_translate(
        self, text: str, src: Language, dst: Language, session: ClientSession
    ) -> Optional[TranslationUnit]:
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
        response = await self.translate(
            text,
            src_language_code,
            dst_language_code,
            session,
        )
        if response is None:
            return None

        translated_text, url = response
        print(f"{self.__class__.__name__} : {text}")
        return TranslationUnit(translated_text, self.service_name, url)

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

    services: ClassVar[list[TranslationService]] = []

    @classmethod
    def register_service(
        cls, service_type: Type[TranslationService]
    ) -> Type[TranslationService]:
        "Decorator for service registration."
        service = service_type()
        cls.services.append(service)
        return service_type

    def translate(self, text: str) -> Optional[TranslationsToBothLanguages]:
        """
        Detects the language of the text and returns aggregated results of translation
        to all supported languages via all registered services.
        """
        src = detect_language(text)
        if src is None:
            return None
        dst_1, dst_2 = [x for x in Language if x != src]
        return TranslationsToBothLanguages(
            src,
            self.translate_to_the_language(text, src, dst_1),
            self.translate_to_the_language(text, src, dst_2),
        )

    def translate_to_the_language(
        self, text: str, src: Language, dst: Language
    ) -> TranslationsToTheSameLanguage:
        translations = asyncio.run(self._translate_to_the_language(text, src, dst))
        return TranslationsToTheSameLanguage(
            dst, [t for t in translations if t is not None]
        )

    async def _translate_to_the_language(
        self, text: str, src: Language, dst: Language
    ) -> list[Optional[TranslationUnit]]:
        to_gather = []
        async with ClientSession(headers={"UserAgent": UserAgent().random}) as session:
            for service in self.services:
                to_gather.append(service.wrap_translate(text, src, dst, session))
            return await asyncio.gather(*to_gather)


@Translator.register_service
class DemekRu(TranslationService):
    URL = "https://demek.ru/soz/?q={}"

    @property
    def service_name(self) -> str:
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
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        query = "+".join(text.split())
        url = self.URL.format(query)
        html = await make_request(url, session)
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")
        search_result = soup.find("div", "item_bsc")
        if search_result is None:
            return None
        translated_text = search_result.get_text()
        return translated_text, url


@Translator.register_service
class GlosbeCom(TranslationService):
    URL = "https://glosbe.com/{}/{}/{}"

    @property
    def service_name(self) -> str:
        return "glosbe.com"

    async def translate(
        self,
        text: str,
        src_language_code: str,
        dst_language_code: str,
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        query = "%20".join(text.split())
        url = self.URL.format(src_language_code, dst_language_code, query)
        html = await make_request(url, session)
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")
        summary_section = soup.find("p", attrs={"id": "content-summary"})
        if summary_section is None:
            return None
        bold_text = summary_section.find("strong")
        if bold_text is None or isinstance(bold_text, int):
            return None
        translated_text = bold_text.get_text()
        return translated_text, url


@dataclass
class GoogleTranslateClient:
    client: translate.Client

    @classmethod
    def from_config(cls, path: str = "config.ini") -> "GoogleTranslateClient":
        config = ConfigParser()
        config.read(path)
        gcloud_key_path = config["GOOGLE TRANSLATE"]["Key path"]
        return cls(
            translate.Client.from_service_account_json(gcloud_key_path),
        )


@Translator.register_service
class GoogleTranslate(TranslationService):
    URL = "https://translate.google.com/?sl={}&tl={}&text={}&op=translate"

    def __init__(self) -> None:
        super().__init__()
        self.client = GoogleTranslateClient.from_config()

    @property
    def service_name(self) -> str:
        return "google.com"

    async def translate(
        self,
        text: str,
        src_language_code: str,
        dst_language_code: str,
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        response = self.client.client.translate(
            values=text,
            source_language=src_language_code,
            target_language=dst_language_code,
        )
        translated_text = response["translatedText"]

        query = "%20".join(text.split())
        url = self.URL.format(src_language_code, dst_language_code, query)
        return translated_text, url


@Translator.register_service
class TurkcesozlukNet(TranslationService):
    URL = "https://www.turkcesozluk.net/index.php?word={}"

    @property
    def service_name(self) -> str:
        return "turkcesozluk.net"

    async def translate(
        self,
        text: str,
        src_language_code: str,
        dst_language_code: str,
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        query = "+".join(text.split())
        url = self.URL.format(query)

        html = await make_request(url, session)
        if html is None:
            return None

        name_attr = src_language_code + dst_language_code
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"name": name_attr})
        if table is None or isinstance(table, NavigableString):
            return None

        table_content = table.find_all("tr")[1]
        first_row = table_content.find("tr")
        cell = first_row.find_all("td")[1]
        list = cell.find("ul", {"class": "ulc"})
        if list is None:
            return cell.get_text(), url
        points = list.find_all("li", limit=5)

        translated_text = " ".join(p.get_text() for p in points)
        return translated_text, url


@Translator.register_service
class TurengCom(TranslationService):
    URL = "https://tureng.com/en/turkish-english/{}"

    @property
    def service_name(self) -> str:
        return "tureng.com"

    async def translate(
        self,
        text: str,
        src_language_code: str,
        dst_language_code: str,
        session: ClientSession,
    ) -> Optional[tuple[str, str]]:
        query = "%20".join(text.split())
        url = self.URL.format(query)

        html = await make_request(url, session)
        if html is None:
            return None

        string = f"{dst_language_code} {src_language_code} dictionary".title()
        dst_language = Language[dst_language_code]
        soup = BeautifulSoup(html, "html.parser")

        def h2_with_right_text(tag: Tag) -> bool:
            return tag.name == "h2" and string in tag.get_text()

        h2 = soup.find(h2_with_right_text)
        if h2 is None:
            return None

        before_table = h2.next_sibling
        if before_table is None:
            return None
        table = before_table.next_sibling
        if table is None:
            return None
        translations = table.find_all_next(
            "td", {"lang": ISO_639_codes[dst_language]}, limit=5
        )
        translated_text = "; ".join([t.get_text().strip() for t in translations])
        return translated_text, url

    @property
    def supported_languages(self) -> set[tuple[Language, Language]]:
        return {
            (Language.english, Language.turkish),
            (Language.turkish, Language.english),
        }

    @property
    def language_encoding(self) -> dict[Language, str]:
        return {Language.english: "english", Language.turkish: "turkish"}
