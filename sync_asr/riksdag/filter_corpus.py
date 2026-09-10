# Copyright (c) 2026 Jim O'Regan for Språkbanken Tal
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
Pre-filter metadata jsonl to identify chunks where the official transcript
matches one or both ASR outputs, and classify the nature of any residual
difference.

Match categories (assigned independently per ASR system):
  exact       - normalised texts are identical
  near        - WER <= near_threshold after normalisation
  norm_diff   - residual tokens look like normalisation artefacts
                (digits vs. spelled-out numbers, abbreviations)
  conj_join   - the difference is an inserted coordinating conjunction
                that joins two clauses present separately in the reference
  mismatch    - does not fall into the above

The 'exact' and 'near' categories form the initial foundation corpus.
'norm_diff' and 'conj_join' are candidates for subsequent passes.
"""
import argparse
import json
import re
import sys
from collections import Counter
from enum import Enum
from pathlib import Path


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_SV_COORD_CONJ = re.compile(r"\b(och|men|samt|eller)\b")

_DIGIT_RE = re.compile(r"\b\d+\b")


def normalize(text):
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


def _token_diff(ref_tokens, hyp_tokens):
    """Return (only_in_ref, only_in_hyp) as multisets."""
    ref_counts = Counter(ref_tokens)
    hyp_counts = Counter(hyp_tokens)
    only_ref = ref_counts - hyp_counts
    only_hyp = hyp_counts - ref_counts
    return only_ref, only_hyp


def _looks_like_norm_diff(only_ref, only_hyp):
    """
    Heuristic: the residual tokens are plausibly a normalisation difference
    if the differing tokens are digits on one side and non-digit words of
    similar length on the other, or if one side is empty (pure insertion of
    a normalised form).
    """
    if not only_ref and not only_hyp:
        return True
    ref_has_digits = any(_DIGIT_RE.fullmatch(t) for t in only_ref)
    hyp_has_digits = any(_DIGIT_RE.fullmatch(t) for t in only_hyp)
    if ref_has_digits or hyp_has_digits:
        return True
    return False


def _looks_like_conj_join(ref_norm, hyp_norm):
    """
    Heuristic: the ASR output contains a coordinating conjunction at a
    position where the reference has a clause boundary (approximated by
    the conjunction being absent from the reference but present in the hyp,
    and being the sole or dominant difference).
    """
    ref_tokens = set(ref_norm.split())
    conj_removed = _SV_COORD_CONJ.sub("", hyp_norm)
    conj_removed = _SPACE_RE.sub(" ", conj_removed).strip()
    if conj_removed == ref_norm:
        return True
    only_ref, only_hyp = _token_diff(ref_norm.split(), hyp_norm.split())
    conj_tokens = {"och", "men", "samt", "eller"}
    extra_in_hyp = set(only_hyp.keys()) - conj_tokens
    if not extra_in_hyp and only_hyp:
        return True
    return False


class MatchCategory(str, Enum):
    EXACT = "exact"
    NEAR = "near"
    NORM_DIFF = "norm_diff"
    CONJ_JOIN = "conj_join"
    MISMATCH = "mismatch"


def categorise(rec, near_threshold=0.05):
    """
    Return (whisper_category, wav2vec_category) for a metadata record.
    Uses text_normalized from the record if present, otherwise normalises
    the text field.
    """
    ref = rec.get("text_normalized") or normalize(rec.get("text", ""))
    whisper_norm = normalize(rec.get("whisper_transcription", ""))
    wav2vec_norm = normalize(rec.get("wav2vec_transcription", ""))

    def _cat(asr_norm, wer_key):
        if asr_norm == ref:
            return MatchCategory.EXACT
        wer = rec.get(wer_key, 1.0)
        if wer <= near_threshold:
            return MatchCategory.NEAR
        ref_tokens = ref.split()
        asr_tokens = asr_norm.split()
        only_ref, only_hyp = _token_diff(ref_tokens, asr_tokens)
        if _looks_like_norm_diff(only_ref, only_hyp):
            return MatchCategory.NORM_DIFF
        if _looks_like_conj_join(ref, asr_norm):
            return MatchCategory.CONJ_JOIN
        return MatchCategory.MISMATCH

    return _cat(whisper_norm, "wer_whisper"), _cat(wav2vec_norm, "wer_wav2vec")


_FOUNDATION = {MatchCategory.EXACT, MatchCategory.NEAR}
_LATER_PASS = {MatchCategory.NORM_DIFF, MatchCategory.CONJ_JOIN}


def is_foundation(whisper_cat, wav2vec_cat):
    return whisper_cat in _FOUNDATION or wav2vec_cat in _FOUNDATION


def is_later_pass(whisper_cat, wav2vec_cat):
    return (whisper_cat in _LATER_PASS or wav2vec_cat in _LATER_PASS) and not is_foundation(whisper_cat, wav2vec_cat)


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", nargs="+", help="Metadata jsonl file(s)")
    parser.add_argument(
        "--near-threshold", type=float, default=0.05,
        help="WER at or below which a match is considered 'near' (default: 0.05)"
    )
    parser.add_argument(
        "--emit", choices=["foundation", "later", "all"], default="all",
        help="Which records to write to stdout as jsonl (default: all, with category fields added)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print category counts to stderr"
    )
    return parser.parse_args()


def main():
    args = get_args()

    paths = [Path(p) for p in args.jsonl]
    for p in paths:
        if not p.exists():
            print(f"Error: {p} does not exist", file=sys.stderr)
            sys.exit(1)

    counts = Counter()

    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                whisper_cat, wav2vec_cat = categorise(rec, args.near_threshold)
                counts[(whisper_cat.value, wav2vec_cat.value)] += 1

                foundation = is_foundation(whisper_cat, wav2vec_cat)
                later = is_later_pass(whisper_cat, wav2vec_cat)

                if args.emit == "foundation" and not foundation:
                    continue
                if args.emit == "later" and not later:
                    continue

                rec["match_whisper"] = whisper_cat.value
                rec["match_wav2vec"] = wav2vec_cat.value
                rec["match_foundation"] = foundation
                rec["match_later_pass"] = later
                print(json.dumps(rec, ensure_ascii=False))

    if args.stats:
        print("\nwhisper_cat\twav2vec_cat\tcount", file=sys.stderr)
        for (wh, w2v), n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"{wh}\t{w2v}\t{n}", file=sys.stderr)
        total = sum(counts.values())
        foundation = sum(n for (wh, w2v), n in counts.items()
                         if wh in ("exact", "near") or w2v in ("exact", "near"))
        later = sum(n for (wh, w2v), n in counts.items()
                    if (wh in ("norm_diff", "conj_join") or w2v in ("norm_diff", "conj_join"))
                    and not (wh in ("exact", "near") or w2v in ("exact", "near")))
        print(f"\ntotal: {total}  foundation: {foundation} ({100*foundation//total}%)  later_pass: {later} ({100*later//total}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
