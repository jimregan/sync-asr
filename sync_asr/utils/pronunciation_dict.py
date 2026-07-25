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
"""
Pluggable pronunciation dictionaries, used as a post-hoc confidence/QC
signal on aligner output: given a (word, IPA) pair produced elsewhere
(e.g. extract_pronunciation_pairs.py), look up what one or more reference
dictionaries say the word should sound like, and score the agreement.
"""
import json
from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, Optional, Set


class PronunciationDictionary(ABC):
    """A source of word -> known IPA pronunciation(s)."""

    @abstractmethod
    def lookup(self, word: str) -> Set[str]:
        """Return the known IPA pronunciation variants for `word` (empty set if unknown)."""


class DictPronunciationDictionary(PronunciationDictionary):
    """Wraps a plain {word: {ipa, ...}} mapping."""

    def __init__(self, mapping: Dict[str, Set[str]]):
        self._mapping = mapping

    def lookup(self, word: str) -> Set[str]:
        return set(self._mapping.get(word, set()))


class NSTLexiconDictionary(DictPronunciationDictionary):
    """A DictPronunciationDictionary sourced from the NST Swedish lexicon."""

    @classmethod
    def from_lexicon(cls, lexicon: list):
        from .nst_lexicon import clean_lexicon
        return cls(clean_lexicon(lexicon))

    @classmethod
    def from_cleaned_json(cls, path: Path):
        with open(path) as f:
            raw = json.load(f)
        return cls({word: set(variants) for word, variants in raw.items()})


class BraxenDictionary(DictPronunciationDictionary):
    """A DictPronunciationDictionary sourced from the Braxen Swedish lexicon."""

    @classmethod
    def from_tsv(cls, path: Path):
        from .braxen_lexicon import parse_braxen_tsv
        return cls(parse_braxen_tsv(path))


class CompositeDictionary(PronunciationDictionary):
    """Unions lookups across one or more underlying dictionaries."""

    def __init__(self, dictionaries: Iterable[PronunciationDictionary]):
        self._dictionaries = list(dictionaries)

    def lookup(self, word: str) -> Set[str]:
        result = set()
        for dictionary in self._dictionaries:
            result |= dictionary.lookup(word)
        return result


class TransformingPronunciationDictionary(PronunciationDictionary):
    """
    Wraps another dictionary and expands each of its entries through one
    or more transformation rules (e.g. sync_asr.riksdag.phonetic_rule.Rule
    instances, or anything with a compatible `.apply(ipa) -> List[str]`)
    to also recognise connected-speech variants the base dictionary only
    has in citation form.
    """

    def __init__(self, inner: PronunciationDictionary, rules: Iterable):
        self._inner = inner
        self._rules = list(rules)

    def lookup(self, word: str) -> Set[str]:
        variants = set(self._inner.lookup(word))
        frontier = set(variants)
        for rule in self._rules:
            next_frontier = set()
            for ipa in frontier:
                next_frontier.update(rule.apply(ipa))
            variants |= next_frontier
            frontier = next_frontier
        return variants


def best_match_score(candidate_ipa: str, dictionary_variants: Set[str]) -> Optional[float]:
    """
    Score how well `candidate_ipa` agrees with a dictionary's known
    variants for the word it came from. 1.0 for an exact match, otherwise
    the best SequenceMatcher ratio across variants. None if the word is
    out-of-vocabulary for the dictionary (nothing to validate against).
    """
    if not dictionary_variants:
        return None
    if candidate_ipa in dictionary_variants:
        return 1.0
    return max(SequenceMatcher(None, candidate_ipa, variant).ratio() for variant in dictionary_variants)
