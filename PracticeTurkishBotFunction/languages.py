from enum import Enum, auto
from string import ascii_letters
from typing import Optional


PUNCTUATION_SYMBOLS = set(" ,.")
ENGLISH_SYMBOLS = set(ascii_letters) | PUNCTUATION_SYMBOLS
TURKISH_SYMBOLS = (ENGLISH_SYMBOLS | set("âçÇğĞıİöÖşŞüÜ")) - set("qQwWxX")
RUSSIAN_SYMBOLS = (
    set("аАбБвВгГдДеЕёЁжЖзЗиИйЙкКлЛмМнНоОпПрРсСтТуУфФхХцЦчЧшШщЩъЪыЫьЬэЭюЮяЯ")
    | PUNCTUATION_SYMBOLS
)


class Language(str, Enum):
    russian = auto()
    turkish = auto()
    english = auto()


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


TURKISH_UPPER_TO_LOWER = {
    "Ç": "ç",
    "Ğ": "ğ",
    "I": "ı",
    "İ": "i",
    "Ö": "ö",
    "Ş": "ş",
    "Ü": "ü",
}


def lowercase(text: str, language: Optional[Language]) -> str:
    match language:
        case Language.turkish:
            for k, v in TURKISH_UPPER_TO_LOWER.items():
                text = text.replace(k, v)
            return text.lower()
        case _:
            return text.lower()
