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
Tests use real rows copied verbatim from braxen-sv.tsv (Braxen 1.0,
Tånnander & Edlund 2025), not synthetic data.
"""
from sync_asr.utils.braxen_lexicon import BASE_TO_IPA, braxen_to_ipa, parse_braxen_tsv

# Real rows, verbatim, from braxen-sv.tsv.
_REAL_ROWS = [
    "Caroline\tk 'ae . rh ex . l ai n\tPM NOM\teng\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t626437",
    "Caroline\tk a . r oh . l 'i: n\tPM NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t626438",
    "Karoline\tk a . r oh . l 'i: n\tPM NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t642580",
    "björn\tb j 'oe: rn\tNN UTR SIN IND NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t50051",
    'bollar\tb "o . l ,a r\tNN UTR PLU IND NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t53934',
    'dalbana\td "a: l - b ,a: . n a\tNN UTR SIN IND NOM\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t72248',
    "'Abdu'l-Bahá\ta b . d uu l ~ b a . h 'aa:\tPM NOM\tara\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t676133",
    '$antal\td \'o . l a r | "a n . t ,a: l\tNN\tswe\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t732346',
    # the one real malformed row in the source file (28 tab-separated fields, line 297594)
    "dru\ttvo\td r 'u rs . t v o\tNN\tcze\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t-\t0\t-\t-\t-\t-\t-\t-\t-\t-\t-\t805651",
]


def test_base_to_ipa_covers_documented_phonemes():
    # spot-check a few entries against Braxen's own phoneme table
    # (docs/adoc/includes/phonemes.tsv)
    assert BASE_TO_IPA["rd"] == "ɖ"
    assert BASE_TO_IPA["rn"] == "ɳ"
    assert BASE_TO_IPA["a:"] == "ɑː"
    assert BASE_TO_IPA["au"] == "aʊ"


def test_braxen_to_ipa_strips_stress_and_boundaries():
    assert braxen_to_ipa("k 'ae . rh ex . l ai n") == "kæɾəlaɪn"
    assert braxen_to_ipa("k a . r oh . l 'i: n") == "karoliːn"
    assert braxen_to_ipa("b j 'oe: rn") == "bjœːɳ"
    assert braxen_to_ipa('b "o . l ,a r') == "bɔlar"
    assert braxen_to_ipa('d "a: l - b ,a: . n a') == "dɑːlbɑːna"
    assert braxen_to_ipa("a b . d uu l ~ b a . h 'aa:") == "abdɵlbahaː"
    assert braxen_to_ipa('d \'o . l a r | "a n . t ,a: l') == "dɔlarantɑːl"


def test_parse_braxen_tsv(tmp_path):
    path = tmp_path / "braxen-sv.tsv"
    path.write_text("#\n" + "\n".join(_REAL_ROWS) + "\n", encoding="utf-8")

    lexicon = parse_braxen_tsv(path)

    # keys are lowercase-folded (see parse_braxen_tsv docstring)
    assert lexicon["caroline"] == {"kæɾəlaɪn", "karoliːn"}
    assert lexicon["karoline"] == {"karoliːn"}
    assert lexicon["björn"] == {"bjœːɳ"}


def test_parse_braxen_tsv_skips_malformed_row(tmp_path):
    # the real source file has exactly one row with 28 fields instead of 27
    # (an extra tab splits "dru\ttvo" instead of a single orthography field);
    # it must be skipped, not mis-parsed.
    path = tmp_path / "braxen-sv.tsv"
    path.write_text("\n".join(_REAL_ROWS) + "\n", encoding="utf-8")

    lexicon = parse_braxen_tsv(path)

    assert "dru" not in lexicon
