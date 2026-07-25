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
Regression tests built from real wav2vec2-nolm / phonetic-model output
pairs (Riksdag foundation corpus), not synthetic data.
"""
from sync_asr.riksdag.extract_pronunciation_pairs import extract_pairs


def test_real_sample_tack_fru_talman():
    w2v_chunks = [
        {"text": "TACK", "timestamp": [11.96, 12.3]},
        {"text": "FRU", "timestamp": [12.4, 12.52]},
        {"text": "TALMAN", "timestamp": [12.6, 13.12]},
    ]
    phon_chunks = [
        {"text": "tak", "timestamp": [11.96, 12.34]},
        {"text": "frʉː", "timestamp": [12.42, 12.52]},
        {"text": "tɑːlman", "timestamp": [12.62, 13.18]},
    ]
    meta = {"text_normalized": "tack fru talman"}

    pairs, markers = extract_pairs(meta, phon_chunks, w2v_chunks)

    assert [(p.word, p.ipa) for p in pairs] == [
        ("tack", "tak"),
        ("fru", "frʉː"),
        ("talman", "tɑːlman"),
    ]
    assert markers == []


def test_real_sample_forste_talare_with_splits_and_markers():
    w2v_chunks = [
        {"text": "FÖRSTE", "timestamp": [0.12, 0.36]},
        {"text": "TALARE", "timestamp": [0.44, 0.84]},
        {"text": "KAROLIN", "timestamp": [1.24, 1.7]},
        {"text": "TJUVER", "timestamp": [1.84, 2.22]},
        {"text": "KDE", "timestamp": [2.44, 2.76]},
        {"text": "VARSÅ", "timestamp": [3.04, 3.28]},
        {"text": "GOD", "timestamp": [3.34, 3.52]},
    ]
    phon_chunks = [
        {"text": "<hes>", "timestamp": [0.02, 0.04]},
        {"text": "fœ̞sta", "timestamp": [0.12, 0.36]},
        {"text": "tɑːlaə", "timestamp": [0.44, 0.84]},
        {"text": "<pa>", "timestamp": [0.9, 0.94]},
        {"text": "kaʊliːn", "timestamp": [1.24, 1.72]},
        {"text": "ɕyːlɔ", "timestamp": [1.86, 2.14]},
        {"text": "koː", "timestamp": [2.44, 2.52]},
        {"text": "ɖeː", "timestamp": [2.7, 2.74]},
        {"text": "vɑː", "timestamp": [3.04, 3.08]},
        {"text": "soː", "timestamp": [3.22, 3.28]},
        {"text": "ɡuːɖ", "timestamp": [3.34, 3.52]},
    ]
    meta = {"text_normalized": "förste talare karolin tjuver kde varså god"}

    pairs, markers = extract_pairs(meta, phon_chunks, w2v_chunks)

    assert [(p.word, p.ipa) for p in pairs] == [
        ("förste", "fœ̞sta"),
        ("talare", "tɑːlaə"),
        ("karolin", "kaʊliːn"),
        ("tjuver", "ɕyːlɔ"),
        ("kde", "koː ɖeː"),
        ("varså", "vɑː soː"),
        ("god", "ɡuːɖ"),
    ]
    # KDE and VARSÅ each pick up two phonetic tokens (letter-spelled party
    # code, and a two-syllable rendering) rather than being force-matched 1:1.
    assert [t.text for t in pairs[4].tokens] == ["koː", "ɖeː"]
    assert [t.text for t in pairs[5].tokens] == ["vɑː", "soː"]

    # <hes> (before any word) and <pa> (between TALARE and KAROLIN) fall in
    # gaps with no corresponding wav2vec word, so they surface as markers
    # instead of being silently dropped.
    assert [(m.text, m.start_ms, m.end_ms) for m in markers] == [
        ("<hes>", 20, 40),
        ("<pa>", 900, 940),
    ]


def test_bracket_token_inside_word_span_is_kept_in_ipa():
    # Synthetic (not real corpus data): covers the other branch of bracket
    # handling, where the tag's timing genuinely falls inside a word's
    # aligned group rather than in a gap between words. Neither real sample
    # above exercises this path.
    w2v_chunks = [{"text": "WORD", "timestamp": [0.0, 1.0]}]
    phon_chunks = [
        {"text": "wo", "timestamp": [0.0, 0.4]},
        {"text": "<hes>", "timestamp": [0.4, 0.5]},
        {"text": "rd", "timestamp": [0.5, 1.0]},
    ]
    meta = {"text_normalized": "word"}

    pairs, markers = extract_pairs(meta, phon_chunks, w2v_chunks)

    assert markers == []
    assert len(pairs) == 1
    assert pairs[0].ipa == "wo <hes> rd"
