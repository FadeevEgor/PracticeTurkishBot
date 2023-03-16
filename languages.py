from enum import Enum, auto
from string import ascii_lowercase
from typing import Optional

from emoji import emojize


PUNCTUATION_SYMBOLS = set(" ,.")
ENGLISH_SYMBOLS = set(ascii_lowercase) | PUNCTUATION_SYMBOLS
TURKISH_SYMBOLS = (set(ascii_lowercase) | set("âçğıiöşü") | PUNCTUATION_SYMBOLS) - set("qwx")
RUSSIAN_SYMBOLS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя") | PUNCTUATION_SYMBOLS


class Language(str, Enum):
    russian = auto()
    turkish = auto()
    english = auto()


def detect_language(text: str) -> Optional[Language]:
    "Detects language using set of symbols"
    symbols = set(text.lower())
    if symbols < TURKISH_SYMBOLS:
        return Language.turkish
    if symbols < RUSSIAN_SYMBOLS:
        return Language.russian
    if symbols < ENGLISH_SYMBOLS:
        return Language.english
    return None


ISO_639_codes: dict[Language, str] = {
    Language.turkish: "tr",
    Language.russian: "ru",
    Language.english: "en",
}


genitive_cases: dict[Language, str] = {
    Language.turkish: "турецкого",
    Language.russian: "русского",
    Language.english: "английского",
}

lang_to_flag: dict[Language, str] = {
    Language.russian: emojize(":Russia:"),
    Language.turkish: emojize(":Turkey:"),
    Language.english: emojize(":United_Kingdom:"),   
}
