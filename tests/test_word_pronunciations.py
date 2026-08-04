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
Real data: the first six words of item CA20011 (wav2vec2, phonetic-model,
and corrected-reference-transcript output from a real storspigg corpus
run), copied verbatim. Expected pronunciations/annotations below were
read off this module's own verified output against that real data, not
invented.
"""
import json

from sync_asr.elements import TimedWord
from sync_asr.utils.pronunciation_dict import DictPronunciationDictionary
from sync_asr.word_pronunciations import (
    WordPronunciation,
    align_reference_timing,
    build_word_pronunciations,
    extract_word_pronunciations,
    load_hf_chunks,
)

_REF_WORDS = ["information", "om", "upphovsrättslagen", "och", "om", "talboken"]

_HYP_WORDS = [
    TimedWord(0.62, 1.36, "information"),
    TimedWord(1.56, 1.7, "om"),
    TimedWord(1.98, 3.18, "upphovsrättslagen"),
    TimedWord(3.32, 3.44, "och"),
    TimedWord(3.56, 3.62, "om"),
    TimedWord(3.76, 4.46, "talboken"),
]

_PHONES = [
    TimedWord(0.6, 1.4, "ɪnfɔmaʂuːn"),
    TimedWord(1.54, 1.8, "ɔm"),
    TimedWord(1.96, 3.2, "ɵphʊvs<v>retslɑːɡən"),
    TimedWord(3.3, 3.5, "ɔk"),
    TimedWord(3.54, 3.66, "ɔm"),
    TimedWord(3.76, 4.5, "tɑːlbuːkən"),
]

# real wav2vec chunk JSON, verbatim (CA20011.json's first 6 chunks)
_HF_CHUNKS_JSON = json.dumps({
    "text": "",
    "chunks": [
        {"text": "INFORMATION", "timestamp": [0.62, 1.36]},
        {"text": "OM", "timestamp": [1.56, 1.7]},
        {"text": "UPPHOVSRÄTTSLAGEN", "timestamp": [1.98, 3.18]},
        {"text": "OCH", "timestamp": [3.32, 3.44]},
        {"text": "OM", "timestamp": [3.56, 3.62]},
        {"text": "TALBOKEN", "timestamp": [3.76, 4.46]},
        {"text": "TRUNCATED", "timestamp": [None, None]},
    ],
})


def test_load_hf_chunks_keeps_seconds_and_drops_null_timestamps(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(_HF_CHUNKS_JSON, encoding="utf-8")

    words = load_hf_chunks(path)

    assert len(words) == 6  # the null-timestamp entry is dropped
    assert (words[0].start_time, words[0].end_time, words[0].text) == (0.62, 1.36, "INFORMATION")


def test_align_reference_timing_carries_hyp_timing_onto_ref_text():
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)

    assert [w.text for w in timed] == _REF_WORDS
    assert (timed[0].start_time, timed[0].end_time) == (0.62, 1.36)
    assert (timed[2].start_time, timed[2].end_time) == (1.98, 3.18)


def test_build_word_pronunciations_real_excerpt():
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    pairs = build_word_pronunciations(timed, _PHONES, metadata={"id": "CA20011"})

    assert [(p.word, p.ipa) for p in pairs] == [
        ("information", "ɪnfɔmaʂuːn"),
        ("om", "ɔm"),
        ("upphovsrättslagen", "ɵphʊvsretslɑːɡən"),
        ("och", "ɔk"),
        ("om", "ɔm"),
        ("talboken", "tɑːlbuːkən"),
    ]
    assert all(p.metadata == {"id": "CA20011"} for p in pairs)


def test_build_word_pronunciations_strips_epenthetic_but_flags_it():
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    pairs = build_word_pronunciations(timed, _PHONES)

    upphovs = pairs[2]
    assert upphovs.word == "upphovsrättslagen"
    assert upphovs.has_epenthetic is True
    assert "<v>" not in upphovs.ipa


def test_build_word_pronunciations_annotations_reflect_match_method():
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    pairs = build_word_pronunciations(timed, _PHONES)

    by_word = {p.word: p for p in pairs}
    # talboken's word/phone timings coincide exactly; the rest drift enough
    # to fall back to pass 2 (still correctly resolved, just tagged
    # differently) -- both verified against this module's own real output.
    assert by_word["talboken"].annotations == {"match_method": "exact_timing"}
    assert by_word["information"].annotations == {"match_method": "time_overlap"}


def test_extract_word_pronunciations_full_pipeline_matches_two_step_version():
    one_shot = extract_word_pronunciations(_REF_WORDS, _HYP_WORDS, _PHONES, metadata={"id": "CA20011"})
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    two_step = build_word_pronunciations(timed, _PHONES, metadata={"id": "CA20011"})

    assert [(p.word, p.ipa) for p in one_shot] == [(p.word, p.ipa) for p in two_step]


def test_reference_word_with_no_hyp_correspondence_gets_no_timing():
    # a ref word with no plausible hyp counterpart at all (kind "del")
    # gets dropped, same as an unmatched word in extract_pronunciation_pairs.py
    ref = ["hej", "extra", "då"]
    hyp = [TimedWord(0, 1, "hej"), TimedWord(1, 2, "då")]

    timed = align_reference_timing(ref, hyp)

    assert [w.text for w in timed] == ["hej", "då"]


def test_build_word_pronunciations_no_dictionaries_leaves_dict_matches_empty():
    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    pairs = build_word_pronunciations(timed, _PHONES)

    assert all(p.dict_matches == [] for p in pairs)


def test_build_word_pronunciations_scores_against_multiple_sources_separately():
    # abstract, source-agnostic wiring test -- not a claim about real
    # Swedish pronunciations, just that both sources get their own entry.
    source_a = DictPronunciationDictionary(
        {"information": {("raw-a", "ɪnfɔmaʂuːn")}}, source="a"
    )
    source_b = DictPronunciationDictionary(
        {"information": {("raw-b", "ɪnfɔmaʃuːn")}}, source="b"
    )

    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    pairs = build_word_pronunciations(timed, _PHONES, dictionaries=[source_a, source_b])

    information = next(p for p in pairs if p.word == "information")
    assert len(information.dict_matches) == 2
    by_source = {m.source: m for m in information.dict_matches}
    assert by_source["a"].score == 1.0
    assert by_source["a"].raw == "raw-a"
    assert by_source["b"].score < 1.0


def test_build_word_pronunciations_all_variants_flag():
    source_a = DictPronunciationDictionary(
        {"om": {("raw-1", "ɔm"), ("raw-2", "om")}}, source="a"
    )

    timed = align_reference_timing(_REF_WORDS, _HYP_WORDS)
    best = build_word_pronunciations(timed, _PHONES, dictionaries=[source_a])
    all_variants = build_word_pronunciations(timed, _PHONES, dictionaries=[source_a], best_only=False)

    om_best = next(p for p in best if p.word == "om")
    om_all = next(p for p in all_variants if p.word == "om")
    assert len(om_best.dict_matches) == 1
    assert len(om_all.dict_matches) == 2


def test_extract_word_pronunciations_threads_dictionaries_through():
    source = DictPronunciationDictionary(
        {"talboken": {("raw", "tɑːlbuːkən")}}, source="a"
    )

    pairs = extract_word_pronunciations(_REF_WORDS, _HYP_WORDS, _PHONES, dictionaries=[source])

    talboken = next(p for p in pairs if p.word == "talboken")
    assert len(talboken.dict_matches) == 1
    assert talboken.dict_matches[0].score == 1.0
