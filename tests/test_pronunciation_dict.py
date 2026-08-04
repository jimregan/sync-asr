# Copyright (c) 2026, Jim O'Regan for Språkbanken Tal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

from sync_asr.utils.pronunciation_dict import (
    BraxenDictionary,
    CompositeDictionary,
    DictionaryMatch,
    DictionaryVariant,
    DictPronunciationDictionary,
    NSTLexiconDictionary,
    TransformingPronunciationDictionary,
    best_match_score,
    score_against_dictionaries,
)


class _DropFinalR:
    """Fake rule matching phonetic_rule.Rule's `.apply(ipa) -> List[str]` contract."""

    def apply(self, ipa):
        if ipa.endswith("r"):
            return [ipa, ipa[:-1]]
        return [ipa]


def test_dict_pronunciation_dictionary_lookup():
    d = DictPronunciationDictionary({"hej": {("h ej", "hɛj")}}, source="test")
    assert d.lookup("hej") == {"hɛj"}
    assert d.lookup("missing") == set()


def test_dict_pronunciation_dictionary_lookup_variants_carries_source_and_raw():
    d = DictPronunciationDictionary({"hej": {("h ej", "hɛj")}}, source="test")
    variants = d.lookup_variants("hej")
    assert variants == [DictionaryVariant(source="test", raw="h ej", ipa="hɛj")]
    assert d.lookup_variants("missing") == []


def test_composite_dictionary_unions():
    d1 = DictPronunciationDictionary({"hej": {("h ej", "hɛj")}}, source="a")
    d2 = DictPronunciationDictionary({"hej": {("hej", "hej")}, "da": {("da", "dɑ")}}, source="b")
    composite = CompositeDictionary([d1, d2])
    assert composite.lookup("hej") == {"hɛj", "hej"}
    assert composite.lookup("da") == {"dɑ"}
    assert composite.lookup("nope") == set()


def test_composite_dictionary_preserves_per_source_attribution():
    d1 = DictPronunciationDictionary({"hej": {("h ej", "hɛj")}}, source="a")
    d2 = DictPronunciationDictionary({"hej": {("hej", "hej")}}, source="b")
    composite = CompositeDictionary([d1, d2])
    variants = composite.lookup_variants("hej")
    assert {v.source for v in variants} == {"a", "b"}


def test_transforming_dictionary_expands_variants():
    inner = DictPronunciationDictionary({"har": {("har", "hɑr")}}, source="test")
    transformed = TransformingPronunciationDictionary(inner, [_DropFinalR()])
    assert transformed.lookup("har") == {"hɑr", "hɑ"}
    # the derived variant keeps the originating variant's source/raw
    derived = [v for v in transformed.lookup_variants("har") if v.ipa == "hɑ"][0]
    assert derived.source == "test"
    assert derived.raw == "har"


def test_transforming_dictionary_passes_through_when_no_match():
    inner = DictPronunciationDictionary({"da": {("da", "dɑ")}}, source="test")
    transformed = TransformingPronunciationDictionary(inner, [_DropFinalR()])
    assert transformed.lookup("da") == {"dɑ"}


def test_best_match_score_exact():
    assert best_match_score("hɛj", {"hɛj", "hej"}) == 1.0


def test_best_match_score_partial():
    score = best_match_score("hɛj", {"hej"})
    assert 0.0 < score < 1.0


def test_best_match_score_oov():
    assert best_match_score("hɛj", set()) is None


def test_nst_lexicon_dictionary_from_cleaned_json(tmp_path):
    path = tmp_path / "lexicon.json"
    path.write_text(json.dumps({"hej": ["hɛj", "hej"]}), encoding="utf-8")
    d = NSTLexiconDictionary.from_cleaned_json(path)
    assert d.lookup("hej") == {"hɛj", "hej"}
    assert d.lookup("missing") == set()
    # this format has no separate raw form; raw==ipa rather than fabricated
    assert all(v.raw == v.ipa for v in d.lookup_variants("hej"))
    assert all(v.source == "nst" for v in d.lookup_variants("hej"))


def test_braxen_dictionary_from_tsv(tmp_path):
    # real rows, verbatim, from braxen-sv.tsv
    rows = [
        "björn\tb j 'oe: rn\tNN UTR SIN IND NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t50051",
        "Caroline\tk a . r oh . l 'i: n\tPM NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t626438",
    ]
    path = tmp_path / "braxen-sv.tsv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    d = BraxenDictionary.from_tsv(path)

    assert d.lookup("björn") == {"bjœːɳ"}
    # extract_pronunciation_pairs.py always looks up lowercased ref words,
    # so BraxenDictionary keys are lowercase-folded (see braxen_lexicon.py)
    assert d.lookup("caroline") == {"karoliːn"}
    assert d.lookup("Caroline") == set()
    assert d.lookup("missing") == set()

    variants = d.lookup_variants("björn")
    assert variants == [DictionaryVariant(source="braxen", raw="b j 'oe: rn", ipa="bjœːɳ")]


def test_score_against_dictionaries_best_only_default():
    braxen = DictPronunciationDictionary(
        {"hej": {("h ej", "hɛj"), ("hej", "hej")}}, source="braxen"
    )
    nst = DictPronunciationDictionary({"hej": {("hej", "hej")}}, source="nst")

    matches = score_against_dictionaries("hɛj", "hej", [braxen, nst])

    assert len(matches) == 2  # one per source
    by_source = {m.source: m for m in matches}
    assert by_source["braxen"].score == 1.0
    assert by_source["braxen"].raw == "h ej"
    assert by_source["braxen"].ipa == "hɛj"
    assert by_source["nst"].score < 1.0  # only has the "hej" variant


def test_score_against_dictionaries_all_variants():
    braxen = DictPronunciationDictionary(
        {"hej": {("h ej", "hɛj"), ("hej", "hej")}}, source="braxen"
    )

    matches = score_against_dictionaries("hɛj", "hej", [braxen], best_only=False)

    assert len(matches) == 2
    assert matches[0].score == 1.0  # best-scoring first within the source
    assert all(m.source == "braxen" for m in matches)


def test_score_against_dictionaries_oov_source_contributes_nothing():
    braxen = DictPronunciationDictionary({"hej": {("hej", "hej")}}, source="braxen")
    empty = DictPronunciationDictionary({}, source="empty")

    matches = score_against_dictionaries("hej", "hej", [braxen, empty])

    assert len(matches) == 1
    assert matches[0].source == "braxen"


def test_dictionary_match_is_a_plain_dataclass():
    m = DictionaryMatch(source="braxen", raw="h ej", ipa="hɛj", score=1.0)
    assert (m.source, m.raw, m.ipa, m.score) == ("braxen", "h ej", "hɛj", 1.0)
