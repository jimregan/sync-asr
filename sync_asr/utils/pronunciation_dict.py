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
(e.g. extract_pronunciation_pairs.py, word_pronunciations.py), look up
what one or more reference dictionaries say the word should sound like,
and score the agreement -- against each dictionary source separately,
so a caller can see not just a score but which source produced it and
that source's own unmodified pronunciation string.
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class DictionaryVariant:
    """One pronunciation a dictionary knows for a word. `raw` is the
    unmodified, source-native string (e.g. Braxen's own Base notation);
    `ipa` is its converted form, used for comparison."""
    source: str
    raw: str
    ipa: str


@dataclass(frozen=True)
class DictionaryMatch:
    """A DictionaryVariant scored against a candidate IPA string."""
    source: str
    raw: str
    ipa: str
    score: float


class PronunciationDictionary(ABC):
    """A source of word -> known pronunciation variant(s)."""

    @abstractmethod
    def lookup_variants(self, word: str) -> List[DictionaryVariant]:
        """Return the known pronunciation variants for `word` from this
        source (empty list if unknown)."""

    def lookup(self, word: str) -> Set[str]:
        """Convenience: just the ipa forms, discarding source/raw provenance."""
        return {v.ipa for v in self.lookup_variants(word)}


class DictPronunciationDictionary(PronunciationDictionary):
    """Wraps a plain {word: {(raw, ipa), ...}} mapping, tagged with a source name."""

    def __init__(self, mapping: Dict[str, Set[Tuple[str, str]]], source: str = "unknown"):
        self._mapping = mapping
        self.source = source

    def lookup_variants(self, word: str) -> List[DictionaryVariant]:
        return [DictionaryVariant(self.source, raw, ipa) for raw, ipa in self._mapping.get(word, set())]


class NSTLexiconDictionary(DictPronunciationDictionary):
    """A DictPronunciationDictionary sourced from the NST Swedish lexicon."""

    @classmethod
    def from_lexicon(cls, lexicon: list, source: str = "nst"):
        from .nst_lexicon import clean_lexicon
        return cls(clean_lexicon(lexicon), source=source)

    @classmethod
    def from_cleaned_json(cls, path: Path, source: str = "nst"):
        with open(path) as f:
            raw = json.load(f)
        # this format never carried a source-native raw form separately
        # from the cleaned ipa; raw==ipa here rather than fabricating one.
        mapping = {word: {(ipa, ipa) for ipa in variants} for word, variants in raw.items()}
        return cls(mapping, source=source)


class BraxenDictionary(DictPronunciationDictionary):
    """A DictPronunciationDictionary sourced from the Braxen Swedish lexicon."""

    @classmethod
    def from_tsv(cls, path: Path, source: str = "braxen"):
        from .braxen_lexicon import parse_braxen_tsv
        return cls(parse_braxen_tsv(path), source=source)


class CompositeDictionary(PronunciationDictionary):
    """Unions lookups across one or more underlying dictionaries, preserving each's own source tag."""

    def __init__(self, dictionaries: Iterable[PronunciationDictionary]):
        self._dictionaries = list(dictionaries)

    def lookup_variants(self, word: str) -> List[DictionaryVariant]:
        result: List[DictionaryVariant] = []
        for dictionary in self._dictionaries:
            result.extend(dictionary.lookup_variants(word))
        return result


class TransformingPronunciationDictionary(PronunciationDictionary):
    """
    Wraps another dictionary and expands each of its entries through one
    or more transformation rules (e.g. sync_asr.riksdag.phonetic_rule.Rule
    instances, or anything with a compatible `.apply(ipa) -> List[str]`)
    to also recognise connected-speech variants the base dictionary only
    has in citation form. Expanded variants keep the originating
    variant's source and raw string -- the rule transforms `ipa` only,
    there is no separate "raw" form for a derived variant.
    """

    def __init__(self, inner: PronunciationDictionary, rules: Iterable):
        self._inner = inner
        self._rules = list(rules)

    def lookup_variants(self, word: str) -> List[DictionaryVariant]:
        variants = list(self._inner.lookup_variants(word))
        seen = {(v.source, v.raw, v.ipa) for v in variants}
        frontier = list(variants)
        for rule in self._rules:
            next_frontier = []
            for variant in frontier:
                for new_ipa in rule.apply(variant.ipa):
                    nv = DictionaryVariant(variant.source, variant.raw, new_ipa)
                    next_frontier.append(nv)
                    key = (nv.source, nv.raw, nv.ipa)
                    if key not in seen:
                        seen.add(key)
                        variants.append(nv)
            frontier = next_frontier
        return variants


def _score_variant(candidate_ipa: str, variant: DictionaryVariant) -> float:
    if candidate_ipa == variant.ipa:
        return 1.0
    return SequenceMatcher(None, candidate_ipa, variant.ipa).ratio()


def score_against_dictionaries(
    candidate_ipa: str,
    word: str,
    dictionaries: Iterable[PronunciationDictionary],
    best_only: bool = True,
) -> List[DictionaryMatch]:
    """
    Score `candidate_ipa` against `word`'s known variants in each of
    `dictionaries`, kept separate by source (unlike looking up a
    CompositeDictionary, which would merge sources together and lose
    which one produced a match). A dictionary the word is
    out-of-vocabulary for contributes no entries at all (not a null
    placeholder) -- absence from the result means OOV, not "checked,
    score 0".

    `best_only=True` (default): one DictionaryMatch per dictionary, its
    best-scoring variant. `best_only=False`: every variant from every
    dictionary, each individually scored, best-scoring first within
    each source.
    """
    matches: List[DictionaryMatch] = []
    for dictionary in dictionaries:
        variants = dictionary.lookup_variants(word)
        if not variants:
            continue
        scored = [
            DictionaryMatch(v.source, v.raw, v.ipa, _score_variant(candidate_ipa, v))
            for v in variants
        ]
        if best_only:
            matches.append(max(scored, key=lambda m: m.score))
        else:
            scored.sort(key=lambda m: -m.score)
            matches.extend(scored)
    return matches


def best_match_score(candidate_ipa: str, dictionary_variants: Set[str]) -> Optional[float]:
    """
    Score how well `candidate_ipa` agrees with a flat set of known ipa
    variants (e.g. from PronunciationDictionary.lookup()). 1.0 for an
    exact match, otherwise the best SequenceMatcher ratio across
    variants. None if the word is out-of-vocabulary (nothing to
    validate against). Kept for callers that only need one aggregate
    score and don't care about per-source provenance; see
    score_against_dictionaries() for the source/raw-carrying form.
    """
    if not dictionary_variants:
        return None
    if candidate_ipa in dictionary_variants:
        return 1.0
    return max(SequenceMatcher(None, candidate_ipa, variant).ratio() for variant in dictionary_variants)
