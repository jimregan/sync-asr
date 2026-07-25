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
    DictPronunciationDictionary,
    NSTLexiconDictionary,
    TransformingPronunciationDictionary,
    best_match_score,
)


class _DropFinalR:
    """Fake rule matching phonetic_rule.Rule's `.apply(ipa) -> List[str]` contract."""

    def apply(self, ipa):
        if ipa.endswith("r"):
            return [ipa, ipa[:-1]]
        return [ipa]


def test_dict_pronunciation_dictionary_lookup():
    d = DictPronunciationDictionary({"hej": {"hɛj"}})
    assert d.lookup("hej") == {"hɛj"}
    assert d.lookup("missing") == set()


def test_composite_dictionary_unions():
    d1 = DictPronunciationDictionary({"hej": {"hɛj"}})
    d2 = DictPronunciationDictionary({"hej": {"hej"}, "da": {"dɑ"}})
    composite = CompositeDictionary([d1, d2])
    assert composite.lookup("hej") == {"hɛj", "hej"}
    assert composite.lookup("da") == {"dɑ"}
    assert composite.lookup("nope") == set()


def test_transforming_dictionary_expands_variants():
    inner = DictPronunciationDictionary({"har": {"hɑr"}})
    transformed = TransformingPronunciationDictionary(inner, [_DropFinalR()])
    assert transformed.lookup("har") == {"hɑr", "hɑ"}


def test_transforming_dictionary_passes_through_when_no_match():
    inner = DictPronunciationDictionary({"da": {"dɑ"}})
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
