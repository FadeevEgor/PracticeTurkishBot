from dataclasses import dataclass
from io import StringIO
from typing import List

from httpx import AsyncClient  # type: ignore
from bs4 import BeautifulSoup
from bs4.element import Tag
from emoji import emojize  # type: ignore

URL = "https://www.turkishclass101.com/turkish-phrases/"
TK = emojize(":Turkey:")
GB = emojize(":United_Kingdom:")


@dataclass
class Example:
    turkish: str
    english: str


@dataclass
class WordOfTheDay:
    turkish_word: str
    part_of_speech: str
    english_translation: str
    examples: List[Example]


def _find_div(
    tag: Tag,
    prefix: str,
    affix: str,
) -> Tag:
    return tag.find("div", attrs={"class": f"{prefix}wotd-widget{affix}"})


def _find_all_divs(tag: Tag, prefix: str, affix: str, limit: int) -> List[Tag]:
    return tag.findAll(
        "div", attrs={"class": f"{prefix}wotd-widget{affix}"}, limit=limit
    )


async def parse_url(client: AsyncClient) -> WordOfTheDay:
    response = await client.get(
        URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    )
    soup = BeautifulSoup(response.content, "html.parser")
    widget = _find_div(soup, "", "")
    word = _find_div(widget, "r101-", "__word").text.strip()
    pos = _find_div(widget, "r101-", "__class").text.strip()
    english = _find_div(widget, "r101-", "__english").text.strip()

    example_divs = _find_all_divs(widget, "r101-", "__section", 9)
    examples = []
    for div in example_divs:
        examples.append(
            Example(
                _find_div(div, "r101-", "__word").text.strip(),
                _find_div(div, "r101-", "__english").text.strip(),
            )
        )
    return WordOfTheDay(word, pos, english, examples)


async def word_of_the_day(client: AsyncClient) -> str:
    word = await parse_url(client)
    message = StringIO()

    message.write("<u>Turkish word of today</u>:\n")
    message.write(f"{TK}<b>{word.turkish_word}</b>{TK}\n")
    message.write(
        f"{GB}<b>{word.english_translation}</b>{GB} ({word.part_of_speech})\n"
    )
    message.write("\n")

    message.write("<u>Examples of usage</u>:\n")
    for i, e in enumerate(word.examples, start=1):
        message.write(f"<code>{i}. </code>{TK}{e.turkish} \n")
        message.write(f"<code>   </code>{GB}{e.english} \n")

    return message.getvalue()
