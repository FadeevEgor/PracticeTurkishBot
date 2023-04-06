from dataclasses import dataclass
from io import StringIO
from zeyrek import MorphAnalyzer  # type: ignore
from zeyrek.rulebasedanalyzer import _Single_Analysis  # type: ignore


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


class MorphemeCompressor:
    compressions = {
        "First": "1st",
        "Second": "2nd",
        "Third": "3rd",
        "Person": "Prsn",
    }

    @classmethod
    def compress(cls, name: str) -> str:
        for k, v in cls.compressions.items():
            name = name.replace(k, v)
        return name


class Morphology:
    def __init__(self) -> None:
        self.analyzer = MorphAnalyzer()

    def parse_single_analysis(
        self, word: str, analysis: _Single_Analysis
    ) -> WordAnalysis:
        dict_item = analysis.dict_item
        lemma = dict_item.lemma
        pos = dict_item.primary_pos.name
        morphemes = [Morpheme(m[1], m[0].name) for m in analysis.morphemes]
        return WordAnalysis(word, pos, lemma, morphemes)

    def format_analysis(self, a: WordAnalysis) -> str:
        result = StringIO()
        max_len = max([len(m.value) for m in a.morphemes] + [len(a.word), len(a.lemma)])

        result.write(f"<b>{a.lemma}</b>\n")
        indent = 0
        for i, m in enumerate(a.morphemes):
            symbol = "+" if i else ">"
            value_length = len(m.value)
            value_with_indent = m.value.rjust(indent + value_length).ljust(max_len)
            name_compressed = MorphemeCompressor.compress(m.name)
            result.write(
                f"<code>{symbol}{value_with_indent}|</code>{name_compressed}\n"
            )
            indent += value_length
        result.write(f"<code>={a.word.rjust(max_len)}|</code><b>{a.pos}</b>\n")
        return result.getvalue()

    def extract_analyses(self, word: str) -> list[WordAnalysis]:
        parsed = self.analyzer._parse(word)
        if not parsed:
            return []
        return [self.parse_single_analysis(word, p) for p in parsed]

    def analyze(self, word: str) -> str:
        result = StringIO()
        analyses = self.extract_analyses(word)
        for a in analyses:
            result.write(self.format_analysis(a))
            result.write("\n")
        return result.getvalue().strip()

    def get_lemmas(self, word: str) -> set[str]:
        analyses = self.extract_analyses(word)
        return {a.lemma for a in analyses}

    def check_if_interesting(self, word: str) -> bool:
        lemmas = self.get_lemmas(word)
        if not lemmas:
            return False
        if word in lemmas:
            return False
        return True


def main() -> None:
    word = "yaşındaken"
    morphology = Morphology()
    print(morphology.check_if_interesting(word))
    analysis = morphology.analyze(word)
    print(analysis)


if __name__ == "__main__":
    main()
