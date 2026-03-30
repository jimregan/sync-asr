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
Extract (word, IPA) pairs from foundation-corpus metadata records by
joining wav2vec2-nolm word timestamps with phonetic model output.

For each matching word (official transcript == wav2vec2-nolm word after
normalisation), phonetic tokens whose midpoint falls within the word's
time window are collected and concatenated to form the IPA pronunciation.

Special tokens:
  <hes>  - hesitation; skipped entirely
  <v>    - word-final epenthetic vowel; stripped from IPA output but
           flagged in the record so callers can filter or keep it
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_EPENTHETIC = "<v>"
_HESITATION = "<hes>"


def _normalize(text):
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


def _strip_special(text):
    return text.replace(_EPENTHETIC, "").strip()


def _is_skip(text):
    return text.strip() == _HESITATION


def _midpoint(timestamp):
    return (timestamp[0] + timestamp[1]) / 2


def _within(midpoint, start_s, end_s, tolerance=0.05):
    return (start_s - tolerance) <= midpoint <= (end_s + tolerance)


@dataclass
class PronunciationPair:
    word: str
    ipa: str
    has_epenthetic: bool
    start_ms: int
    end_ms: int
    speaker_id: str
    district: str
    year: Optional[int]
    speech_id: Optional[str]


def extract_pairs(
    meta_rec: dict,
    phonetic_chunks: list,
    wav2vec_chunks: list,
) -> List[PronunciationPair]:
    """
    Extract pronunciation pairs from one metadata record.

    Parameters
    ----------
    meta_rec : dict
        One record from the foundation corpus metadata jsonl.
    phonetic_chunks : list
        The 'chunks' list from the phonetic model jsonl for this segment.
        Each element: {"text": "<IPA>", "timestamp": [start_s, end_s]}
    wav2vec_chunks : list
        The 'chunks' list from the wav2vec2-nolm jsonl for this segment.
        Each element: {"text": "<word>", "timestamp": [start_s, end_s]}
    """
    ref_words = (
        meta_rec.get("text_normalized") or _normalize(meta_rec.get("text", ""))
    ).split()

    w2v_items = [c for c in wav2vec_chunks if not _is_skip(c["text"])]
    w2v_words = [_normalize(c["text"]) for c in w2v_items]

    matcher = SequenceMatcher(None, ref_words, w2v_words, autojunk=False)

    pairs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag not in ("equal", "replace"):
            continue
        ref_slice = ref_words[i1:i2]
        w2v_slice = w2v_items[j1:j2]
        for ref_word, w2v_chunk in zip(ref_slice, w2v_slice):
            if tag == "replace" and _normalize(w2v_chunk["text"]) != ref_word:
                continue
            ts = w2v_chunk["timestamp"]
            if ts[0] is None or ts[1] is None:
                continue
            start_s, end_s = ts[0], ts[1]

            phon_tokens = [
                c for c in phonetic_chunks
                if not _is_skip(c["text"])
                and c["timestamp"][0] is not None
                and c["timestamp"][1] is not None
                and _within(_midpoint(c["timestamp"]), start_s, end_s)
            ]
            if not phon_tokens:
                continue

            has_epenthetic = any(_EPENTHETIC in c["text"] for c in phon_tokens)
            ipa = " ".join(_strip_special(c["text"]) for c in phon_tokens)
            if not ipa:
                continue

            pairs.append(PronunciationPair(
                word=ref_word,
                ipa=ipa,
                has_epenthetic=has_epenthetic,
                start_ms=int(start_s * 1000),
                end_ms=int(end_s * 1000),
                speaker_id=meta_rec.get("speaker_id", ""),
                district=meta_rec.get("district", ""),
                year=meta_rec.get("year"),
                speech_id=meta_rec.get("speech_id"),
            ))

    return pairs


def _load_chunks(path: Path) -> list:
    with open(path) as f:
        data = json.load(f)
    return data.get("chunks", [])


def _resolve_key(meta_rec: dict, key_field: str) -> str:
    value = meta_rec.get(key_field, "")
    return Path(value).stem


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata_jsonl", nargs="+", help="Foundation corpus metadata jsonl file(s)")
    parser.add_argument("--phonetic-dir", type=Path, required=True,
                        help="Directory containing phonetic model jsonl files")
    parser.add_argument("--wav2vec-dir", type=Path, required=True,
                        help="Directory containing wav2vec2-nolm jsonl files")
    parser.add_argument("--phonetic-ext", type=str, default=".phn.json",
                        help="Extension for wav2vec2 phonetic json files")
    parser.add_argument("--wav2vec-ext", type=str, default=".w2v2.json",
                        help="Extension for wav2vec2-nolm json files")
    parser.add_argument(
        "--key-field", default="audio_filepath",
        help="Metadata field whose stem is used as the filename key "
             "(default: audio_filepath)"
    )
    parser.add_argument(
        "--foundation-only", action="store_true",
        help="Skip records where match_foundation is not True "
             "(only relevant if input was produced by filter_corpus.py)"
    )
    parser.add_argument(
        "--no-epenthetic", action="store_true",
        help="Exclude pairs where a word-final epenthetic vowel was detected"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print summary counts to stderr"
    )
    return parser.parse_args()


def main():
    args = get_args()

    phon_dir = args.phonetic_dir
    w2v_dir = args.wav2vec_dir

    total = skipped_filter = skipped_no_file = emitted = 0

    for jsonl_path in args.metadata_jsonl:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                total += 1

                if args.foundation_only and not rec.get("match_foundation", True):
                    skipped_filter += 1
                    continue

                key = _resolve_key(rec, args.key_field)
                phon_file = phon_dir / f"{key}{args.phonetic_ext}"
                w2v_file = w2v_dir / f"{key}{args.wav2vec_ext}"

                if not phon_file.exists() or not w2v_file.exists():
                    skipped_no_file += 1
                    continue

                try:
                    phon_chunks = _load_chunks(phon_file)
                    w2v_chunks = _load_chunks(w2v_file)
                except Exception as e:
                    print(f"Warning: failed to load {key}: {e}", file=sys.stderr)
                    skipped_no_file += 1
                    continue

                pairs = extract_pairs(rec, phon_chunks, w2v_chunks)
                for pair in pairs:
                    if args.no_epenthetic and pair.has_epenthetic:
                        continue
                    print(json.dumps(asdict(pair), ensure_ascii=False))
                    emitted += 1

    if args.stats:
        print(
            f"\ntotal records: {total}  "
            f"skipped (filter): {skipped_filter}  "
            f"skipped (no file): {skipped_no_file}  "
            f"pairs emitted: {emitted}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
