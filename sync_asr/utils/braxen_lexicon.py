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
Parser and Base-notation-to-IPA converter for the Braxen Swedish
pronunciation dictionary (Tånnander & Edlund 2025).

Braxen's TSV format (27 tab-separated fields; field 0 is orthography,
field 1 is the space-separated "Base" pronunciation) and its Base->IPA
phoneme table are documented in the Braxen repository at
docs/adoc/doc-braxen.adoc and docs/adoc/includes/phonemes.tsv.

Base notation marks main stress (accent 1: ', accent 2: ") and
secondary stress (,) as a prefix on the following phoneme, and syllable
(.), compound (-), word (|) and morpheme (~) boundaries as standalone
tokens. braxen_to_ipa() drops all of these to produce a flat phone
sequence, matching the bare-phone style this pipeline's phonetic-model
output uses (no stress or boundary marks) -- see extract_pronunciation_pairs.py.
"""
from typing import Dict, Set

# Base -> IPA, transcribed from Braxen's own phoneme table
# (docs/adoc/includes/phonemes.tsv in the Braxen repository).
BASE_TO_IPA = {
    "p": "p", "b": "b", "t": "t", "rt": "ʈ", "d": "d", "rd": "ɖ",
    "k": "k", "g": "ɡ", "f": "f", "v": "v", "s": "s", "rs": "ʂ",
    "h": "h", "x": "ɧ", "c": "ɕ", "m": "m", "n": "n", "rn": "ɳ",
    "ng": "ŋ", "r": "r", "l": "l", "rl": "ɭ", "j": "j", "w": "w",
    "sh": "ʃ", "zh": "ʒ", "z": "z", "dh": "ð", "th": "θ", "rh": "ɾ",
    "r0": "-", "rx": "ʀ", "tc": "t͡ʃ", "dj": "d͡ʒ", "xx": "x",
    "i:": "iː", "i": "ɪ", "ih": "ɪ̯", "y:": "yː", "y": "ʏ",
    "e:": "eː", "e": "e", "eh": "e̝", "ex": "ə",
    "ä:": "ɛː", "ä": "ɛ", "ae:": "æː", "ae": "æ",
    "ö:": "øː", "ö": "ø", "oe:": "œː", "oe": "œ",
    "u:": "uː", "u": "u", "oh": "o", "o:": "oː", "o": "ɔ",
    "uu:": "ʉː", "uu": "ɵ", "uuh": "ʉ", "uw:": "ʊː", "uw": "ʊ",
    "a:": "ɑː", "a": "a", "aa:": "aː",
    "au": "aʊ", "eu": "ɛʊ", "ei": "eɪ", "ai": "aɪ", "oi": "ɔɪ", "ou": "əʊ",
    "eex": "eə", "iex": "ɪə", "uex": "ʊə",
    "an": "ã", "en": "ɛ̃", "on": "õ", "un": "œ̃",
}

_STRESS_CHARS = set("'\",’”")
_BOUNDARY_TOKENS = {".", "-", "|", "~"}
_FIELD_COUNT = 27


def braxen_to_ipa(pron: str) -> str:
    """
    Convert one Braxen 'Base' pronunciation field to a flat IPA string,
    dropping stress marks and syllable/word/compound/morpheme boundaries.
    Tokens absent from BASE_TO_IPA (data-entry errors in the source
    dictionary; empirically ~1 in 857,000 real entries) pass through
    unchanged rather than raising.
    """
    phones = []
    for tok in pron.split():
        if tok in _BOUNDARY_TOKENS:
            continue
        while tok and tok[0] in _STRESS_CHARS:
            tok = tok[1:]
        if not tok:
            continue
        phones.append(BASE_TO_IPA.get(tok, tok))
    return "".join(phones)


def parse_braxen_tsv(path) -> Dict[str, Set[str]]:
    """
    Parse a Braxen TSV lexicon into {orthography.lower(): {ipa, ...}}.

    Keys are lowercase-folded: this pipeline's reference words are always
    lowercase (see extract_pronunciation_pairs.py's _normalize()), and
    ~22.5% of Braxen's orthography entries carry uppercase only because
    that's the "most frequent casing" (its field 16 marks most of those
    as not case-sensitive) -- folding is what makes them reachable here.
    The ~390 entries Braxen does mark genuinely case-sensitive (e.g.
    Polen/Poland vs polen/pollen) collide under their shared lowercase
    key as a result; this is a known, accepted trade-off for this use.

    Comment lines ("#...", blank) and rows that don't have exactly 27
    fields (the documented Braxen field count) are skipped.
    """
    lexicon: Dict[str, Set[str]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != _FIELD_COUNT:
                continue
            word, pron = fields[0], fields[1]
            lexicon.setdefault(word.lower(), set()).add(braxen_to_ipa(pron))
    return lexicon
