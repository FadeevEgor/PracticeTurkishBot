from enum import Enum, auto
from string import ascii_letters
from typing import Optional

from emoji import emojize  # type: ignore


PUNCTUATION_SYMBOLS = set(" ,.")
ENGLISH_SYMBOLS = set(ascii_letters) | PUNCTUATION_SYMBOLS
TURKISH_SYMBOLS = (ENGLISH_SYMBOLS | set("âçÇğĞıİöÖşŞüÜ")) - set("qQwWxX")
RUSSIAN_SYMBOLS = (
    set("аАбБвВгГдДеЕёЁжЖзЗиИйЙкКлЛмМнНоОпПрРсСтТуУфФхХцЦчЧшШщЩъЪыЫьЬэЭюЮяЯ")
    | PUNCTUATION_SYMBOLS
)


class Language(str, Enum):
    russian = "russian"
    turkish = "turkish"
    english = "english"


def detect_language(text: str) -> Optional[Language]:
    "Detects language using set of symbols"
    symbols = set(text)
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
