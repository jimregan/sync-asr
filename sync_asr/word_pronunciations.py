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
Word-level pronunciations from three independent sources per utterance:
a reference transcript (no timing), a word-timed ASR hypothesis (e.g.
wav2vec2), and a phonetic-model transcription (IPA-ish, also timed).

Pipeline, dataset-agnostic (no paths, no corpus-specific fields):

  1. align_smith_waterman(ref_words, hyp_words) -- the Kaldi-derived
     aligner -- to carry the hypothesis's timing onto the reference
     words wherever they correspond (cor/sub); ins/del give no ref word
     a timestamp and are dropped at this stage.
  2. time_aligner.align() between that now-timed reference-word
     sequence and the phonetic chunks, exactly as
     riksdag/extract_pronunciation_pairs.py already does for Riksdag
     data -- reused here in dataset-agnostic form.
  3. WordPronunciation records, ready for a pronunciation-dictionary
     check (see utils/pronunciation_dict.py) via their `ipa` property.

`metadata` on each record is an open pass-through dict for whatever a
caller wants to carry along (an utterance id, a reader name, ...) --
this module has no opinion on what fields a given corpus needs.
"""
import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .alignment import AlignmentHeuristic, MergedTokenHeuristic, align_smith_waterman
from .elements import TimedElement, TimedWord
from .riksdag.time_aligner import align
from .utils.pronunciation_dict import BraxenDictionary, CompositeDictionary, best_match_score

_EPENTHETIC = "<v>"
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")


def _strip_special(text: str) -> str:
    return text.replace(_EPENTHETIC, "").strip()


def normalize(text: str) -> str:
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


@dataclass
class PhoneticToken:
    text: str
    start_ms: int
    end_ms: int
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WordPronunciation:
    word: str
    word_start_ms: int
    word_end_ms: int
    tokens: List[PhoneticToken]
    has_epenthetic: bool
    annotations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ipa(self) -> str:
        return " ".join(_strip_special(t.text) for t in self.tokens)


def load_hf_chunks(path) -> List[TimedWord]:
    """
    Load a {"text": ..., "chunks": [{"text": ..., "timestamp": [s, e]}]}
    JSON file (wav2vec2-nolm or phonetic-model output) into TimedWords,
    seconds preserved as given (not converted to ms -- unlike
    hf_json_input.HuggingFaceJSON -- so these compose directly with
    time_aligner.align()'s default, seconds-scaled tolerances). Chunks
    with a null timestamp are dropped.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    words = []
    for c in data.get("chunks", []):
        ts = c["timestamp"]
        if ts[0] is None or ts[1] is None:
            continue
        words.append(TimedWord(ts[0], ts[1], c["text"]))
    return words


DEFAULT_REFERENCE_TIMING_HEURISTICS = [MergedTokenHeuristic()]


def align_reference_timing(
    ref_words: List[str],
    hyp_words: List[TimedWord],
    heuristics: Optional[List[AlignmentHeuristic]] = None,
    **smith_waterman_kwargs,
) -> List[TimedWord]:
    """
    Carry `hyp_words`' timing onto `ref_words` via align_smith_waterman:
    for every reference word the aligner corresponds to a hypothesis
    word (kind "cor" or "sub"), emit a TimedWord with the hypothesis's
    timing and the *reference*'s text -- the reference is trusted for
    spelling (e.g. a corrected transcript), the hypothesis for timing.
    Reference words the aligner couldn't place directly (kind "del")
    have no timing of their own -- unless a heuristic bridges them (see
    MergedTokenHeuristic, the default: wav2vec runs two reference words
    together into one hypothesis token often enough that this is worth
    handling by default rather than opt-in) -- and are otherwise
    dropped, same as an unmatched word in extract_pronunciation_pairs.py.

    Where a heuristic bridge and the aligner's own original group both
    cover the same reference word (e.g. the "ab" in the worked
    merged-token example is both the aligner's own literal substitution
    target *and* one half of the heuristic's split), the heuristic's
    interpretation wins -- it exists specifically because the aligner's
    own literal one is known to be wrong here. Both remain in
    `sequence.groups` for any caller who wants the raw, un-heuristic'd
    view; this function picks one so it can build a single ordered
    per-word timeline.
    """
    if heuristics is None:
        heuristics = DEFAULT_REFERENCE_TIMING_HEURISTICS
    sequence = align_smith_waterman(ref_words, hyp_words, heuristics=heuristics, **smith_waterman_kwargs)

    best_by_ref_index: Dict[int, Any] = {}
    for g in sequence.groups:
        if not g.a_indices or not g.b_indices:
            continue
        is_heuristic = bool(g.metadata.get("heuristic"))
        for ai in g.a_indices:
            existing = best_by_ref_index.get(ai)
            if existing is None or (is_heuristic and not existing.metadata.get("heuristic")):
                best_by_ref_index[ai] = g

    timed = []
    for ai in sorted(best_by_ref_index):
        g = best_by_ref_index[ai]
        hyp_word = hyp_words[g.b_indices[0]]
        start = g.metadata.get("split_start_time", hyp_word.start_time)
        end = g.metadata.get("split_end_time", hyp_word.end_time)
        timed.append(TimedWord(start, end, ref_words[ai]))
    return timed


def _align_words_to_phones(
    words: List[TimedElement],
    phones: List[TimedElement],
    start_tolerance: float,
    duration_tolerance: float,
) -> Tuple[Dict[int, List[int]], List[Any]]:
    groups = align(words, phones, start_tolerance=start_tolerance, duration_tolerance=duration_tolerance)
    word_to_phones: Dict[int, List[int]] = {}
    for g in groups:
        if not g.a_indices or not g.b_indices:
            continue
        for ai in g.a_indices:
            word_to_phones.setdefault(ai, []).extend(g.b_indices)
    for indices in word_to_phones.values():
        indices.sort()
    return word_to_phones, groups


def build_word_pronunciations(
    timed_words: List[TimedWord],
    phones: List[TimedElement],
    metadata: Optional[Dict[str, Any]] = None,
    start_tolerance: float = 0.02,
    duration_tolerance: float = 0.05,
) -> List[WordPronunciation]:
    """
    Two-pass time-align `timed_words` (already-timed, e.g. from
    align_reference_timing()) against `phones`, and build one
    WordPronunciation per word with at least one assigned phone.
    """
    word_to_phones, groups = _align_words_to_phones(timed_words, phones, start_tolerance, duration_tolerance)
    group_by_a: Dict[int, Any] = {}
    for g in groups:
        for ai in g.a_indices:
            group_by_a[ai] = g

    pairs = []
    for i, word in enumerate(timed_words):
        phone_indices = word_to_phones.get(i)
        if not phone_indices:
            continue
        tokens = [
            PhoneticToken(text=phones[j].text, start_ms=int(phones[j].start_time * 1000),
                          end_ms=int(phones[j].end_time * 1000))
            for j in phone_indices
        ]
        if not any(_strip_special(t.text) for t in tokens):
            continue
        has_epenthetic = any(_EPENTHETIC in t.text for t in tokens)
        annotations = dict(group_by_a[i].metadata) if i in group_by_a else {}

        pairs.append(WordPronunciation(
            word=word.text,
            word_start_ms=int(word.start_time * 1000),
            word_end_ms=int(word.end_time * 1000),
            tokens=tokens,
            has_epenthetic=has_epenthetic,
            annotations=annotations,
            metadata=dict(metadata) if metadata else {},
        ))
    return pairs


def extract_word_pronunciations(
    ref_words: List[str],
    hyp_words: List[TimedWord],
    phones: List[TimedElement],
    metadata: Optional[Dict[str, Any]] = None,
    smith_waterman_kwargs: Optional[Dict[str, Any]] = None,
    start_tolerance: float = 0.02,
    duration_tolerance: float = 0.05,
) -> List[WordPronunciation]:
    """The full pipeline: reference timing, then phone assignment."""
    timed_words = align_reference_timing(ref_words, hyp_words, **(smith_waterman_kwargs or {}))
    return build_word_pronunciations(
        timed_words, phones, metadata=metadata,
        start_tolerance=start_tolerance, duration_tolerance=duration_tolerance,
    )


def _load_reference(path) -> Dict[str, str]:
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            key, _, text = line.rstrip("\n").partition("\t")
            ref[key] = text
    return ref


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True,
                        help="id<TAB>text file (e.g. a corrected transcript)")
    parser.add_argument("--wav2vec-dir", type=Path, required=True,
                        help="Directory of {id}{--wav2vec-ext} wav2vec2-nolm-style JSON files")
    parser.add_argument("--phonetic-dir", type=Path, required=True,
                        help="Directory of {id}{--phonetic-ext} phonetic-model-style JSON files")
    parser.add_argument("--wav2vec-ext", default=".json")
    parser.add_argument("--phonetic-ext", default=".json")
    parser.add_argument("--start-tolerance", type=float, default=0.02,
                        help="Time-aligner exact-anchor start-time tolerance, in seconds (default: 0.02)")
    parser.add_argument("--duration-tolerance", type=float, default=0.05,
                        help="Time-aligner exact-anchor duration tolerance, in seconds (default: 0.05)")
    parser.add_argument("--braxen-dict", type=Path, action="append", default=[],
                        help="Braxen lexicon TSV file to validate against. May be given more than once; "
                             "adds a dict_match_score field (0-1, null if the word is OOV) to output.")
    parser.add_argument("--stats", action="store_true", help="Print summary counts to stderr")
    return parser.parse_args()


def main():
    args = get_args()

    dictionaries = [BraxenDictionary.from_tsv(p) for p in args.braxen_dict]
    pron_dict = None
    if dictionaries:
        pron_dict = dictionaries[0] if len(dictionaries) == 1 else CompositeDictionary(dictionaries)

    reference = _load_reference(args.reference)

    total = skipped_no_file = emitted = 0
    dict_scores = []

    for item_id, ref_text in sorted(reference.items()):
        total += 1
        w2v_file = args.wav2vec_dir / f"{item_id}{args.wav2vec_ext}"
        phon_file = args.phonetic_dir / f"{item_id}{args.phonetic_ext}"
        if not w2v_file.exists() or not phon_file.exists():
            skipped_no_file += 1
            continue

        try:
            hyp_words = load_hf_chunks(w2v_file)
            phones = load_hf_chunks(phon_file)
        except Exception as e:
            print(f"Warning: failed to load {item_id}: {e}", file=sys.stderr)
            skipped_no_file += 1
            continue

        hyp_words = [TimedWord(w.start_time, w.end_time, normalize(w.text)) for w in hyp_words]
        ref_words = normalize(ref_text).split()

        pairs = extract_word_pronunciations(
            ref_words, hyp_words, phones, metadata={"id": item_id},
            start_tolerance=args.start_tolerance, duration_tolerance=args.duration_tolerance,
        )
        for pair in pairs:
            d = asdict(pair)
            d["ipa"] = pair.ipa
            if pron_dict is not None:
                score = best_match_score(pair.ipa, pron_dict.lookup(pair.word))
                d["dict_match_score"] = score
                if score is not None:
                    dict_scores.append(score)
            print(json.dumps(d, ensure_ascii=False))
            emitted += 1

    if args.stats:
        msg = f"\nitems: {total}  skipped (no file): {skipped_no_file}  pairs emitted: {emitted}"
        if pron_dict is not None:
            checked = len(dict_scores)
            avg = sum(dict_scores) / checked if checked else 0.0
            msg += f"  dict-checked: {checked}  avg dict_match_score: {avg:.3f}"
        print(msg, file=sys.stderr)


if __name__ == "__main__":
    main()
