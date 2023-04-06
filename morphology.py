from zeyrek import MorphAnalyzer
from zeyrek.rulebasedanalyzer import _Single_Analysis

from dataclasses import dataclass
from io import StringIO 


@dataclass(slots=True)
class Morpheme:
    value: str
    name: str

@dataclass(slots=True)
class WordAnalysis:
    word: str
    pos: str
    lemma: str
    morphemes: list[Morpheme]


def parse_single_analysis(word: str, analysis: _Single_Analysis) -> WordAnalysis:
    dict_item = analysis.dict_item
    lemma = dict_item.lemma
    pos = dict_item.primary_pos.name
    morphemes = [Morpheme(m[1], m[0].name) for m in analysis.morphemes]
    return WordAnalysis(
        word,
        pos,
        lemma,
        morphemes
    )

def format_analysis(a: WordAnalysis) -> str:
    result = StringIO()
    max_len = max([len(m.value) for m in a.morphemes] + [len(a.word), len(a.lemma)])
    
    result.write(f"<u>{a.lemma}</u>\n")
    for i, m in enumerate(a.morphemes):
        symbol = "+" if i else ">"
        result.write(f"<code>{symbol} {m.value.ljust(max_len)} | </code>{m.name}\n")
    result.write(f"<code>= {a.word.ljust(max_len)} | </code><b>{a.pos}</b>\n")
    return result.getvalue()
    
def morph_analysis(word: str) -> str | None:
    result = StringIO()
    analyzer = MorphAnalyzer()
    parsed = analyzer._parse(word)
    if not parsed:
        return None
    
    analyses = [parse_single_analysis(word, p) for p in parsed]
    for a in analyses:
        result.write(format_analysis(a))
        result.write("\n")
    
    return result.getvalue().strip()
