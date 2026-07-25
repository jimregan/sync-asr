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
normalisation), phonetic tokens are assigned to it by a two-pass time
alignment (see time_aligner.py) between the full word sequence and the
full phone sequence for the segment: exact start/duration matches are
anchored first, then everything else is grouped by time overlap,
preferring 1:1 but allowing 1:N/N:1 where the overlap is genuinely
ambiguous. The assigned tokens are concatenated to form the IPA
pronunciation.

Special tokens:
  <hes>  - hesitation; treated as epsilon in word alignment (will not
           consume a transcript word) and passed through into the IPA
           output when it falls within a word's time window
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

from ..elements import TimedElement
from ..utils.pronunciation_dict import CompositeDictionary, NSTLexiconDictionary, best_match_score
from .time_aligner import align


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



@dataclass
class PhoneticToken:
    text: str
    start_ms: int
    end_ms: int


@dataclass
class PronunciationPair:
    word: str
    word_start_ms: int
    word_end_ms: int
    tokens: List[PhoneticToken]
    has_epenthetic: bool
    speaker_id: str
    name: str
    gender: str
    role: str
    party: str
    district: str
    year: Optional[int]
    speech_id: Optional[str]
    audio_file: Optional[str]
    audio_start: Optional[int]
    audio_end: Optional[int]
    filestem: Optional[str] = None

    @property
    def ipa(self) -> str:
        return " ".join(_strip_special(t.text) for t in self.tokens)


def _valid_timed_elements(chunks, exclude_text=None):
    """
    Build (original_index, TimedElement) pairs for chunks with a usable
    timestamp, in original order, optionally dropping chunks whose text
    (stripped) equals `exclude_text`.
    """
    out = []
    for idx, c in enumerate(chunks):
        if exclude_text is not None and c["text"].strip() == exclude_text:
            continue
        ts = c["timestamp"]
        if ts[0] is None or ts[1] is None:
            continue
        out.append((idx, TimedElement(ts[0], ts[1], c["text"])))
    return out


def _align_words_to_phones(wav2vec_chunks, phonetic_chunks, start_tolerance, duration_tolerance):
    """
    Two-pass time alignment of word-level wav2vec chunks against
    phone-level phonetic-model chunks for one segment.

    Returns a dict mapping wav2vec_chunks index -> sorted list of
    phonetic_chunks indices assigned to that word. Words with no assigned
    phones (silence, or consumed entirely by a neighbour) are absent.
    """
    a_indexed = _valid_timed_elements(wav2vec_chunks)
    b_indexed = _valid_timed_elements(phonetic_chunks, exclude_text=_HESITATION)

    a_elems = [e for _, e in a_indexed]
    b_elems = [e for _, e in b_indexed]
    a_orig = [i for i, _ in a_indexed]
    b_orig = [i for i, _ in b_indexed]

    groups = align(a_elems, b_elems, start_tolerance=start_tolerance, duration_tolerance=duration_tolerance)

    word_to_phones = {}
    for g in groups:
        if not g.a_indices or not g.b_indices:
            continue
        phon_orig = [b_orig[bi] for bi in g.b_indices]
        for ai in g.a_indices:
            word_to_phones.setdefault(a_orig[ai], []).extend(phon_orig)
    for indices in word_to_phones.values():
        indices.sort()
    return word_to_phones


def extract_pairs(
    meta_rec: dict,
    phonetic_chunks: list,
    wav2vec_chunks: list,
    start_tolerance: float = 0.02,
    duration_tolerance: float = 0.03,
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
    start_tolerance, duration_tolerance : float
        Passed to the two-pass time aligner's exact-anchor pass (seconds).
    """
    ref_words = (
        meta_rec.get("text_normalized") or _normalize(meta_rec.get("text", ""))
    ).split()

    w2v_items = list(wav2vec_chunks)
    w2v_words = [_normalize(c["text"]) for c in w2v_items]

    matcher = SequenceMatcher(None, ref_words, w2v_words, autojunk=False)
    word_to_phones = _align_words_to_phones(w2v_items, phonetic_chunks, start_tolerance, duration_tolerance)

    pairs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag not in ("equal", "replace"):
            continue
        ref_slice = ref_words[i1:i2]
        w2v_slice = w2v_items[j1:j2]
        for offset, (ref_word, w2v_chunk) in enumerate(zip(ref_slice, w2v_slice)):
            if tag == "replace" and _normalize(w2v_chunk["text"]) != ref_word:
                continue
            ts = w2v_chunk["timestamp"]
            if ts[0] is None or ts[1] is None:
                continue
            start_s, end_s = ts[0], ts[1]

            phon_indices = word_to_phones.get(j1 + offset, [])
            phon_tokens = [phonetic_chunks[i] for i in phon_indices]
            if not phon_tokens:
                continue

            has_epenthetic = any(_EPENTHETIC in c["text"] for c in phon_tokens)
            tokens = [
                PhoneticToken(
                    text=c["text"],
                    start_ms=int(c["timestamp"][0] * 1000),
                    end_ms=int(c["timestamp"][1] * 1000),
                )
                for c in phon_tokens
            ]
            if not any(_strip_special(t.text) for t in tokens):
                continue

            filepath = meta_rec.get("audio_filepath", "")
            filestem = Path(filepath).stem if filepath else ""

            pairs.append(PronunciationPair(
                word=ref_word,
                word_start_ms=int(start_s * 1000),
                word_end_ms=int(end_s * 1000),
                tokens=tokens,
                has_epenthetic=has_epenthetic,
                speaker_id=meta_rec.get("speaker_id", ""),
                name=meta_rec.get("name", ""),
                gender=meta_rec.get("gender", ""),
                role=meta_rec.get("role", ""),
                party=meta_rec.get("party", ""),
                district=meta_rec.get("district", ""),
                year=meta_rec.get("year"),
                speech_id=meta_rec.get("speech_id"),
                audio_file=meta_rec.get("audio_file"),
                audio_start=meta_rec.get("start"),
                audio_end=meta_rec.get("end"),
                filestem=filestem,
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
    parser.add_argument(
        "--start-tolerance", type=float, default=0.02,
        help="Time-aligner exact-anchor start-time tolerance, in seconds (default: 0.02)"
    )
    parser.add_argument(
        "--duration-tolerance", type=float, default=0.03,
        help="Time-aligner exact-anchor duration tolerance, in seconds (default: 0.03)"
    )
    parser.add_argument(
        "--pronunciation-dict", type=Path, action="append", default=[],
        help="Cleaned NST-lexicon-style JSON file ({word: [ipa, ...]}) to validate "
             "extracted pronunciations against. May be given more than once; "
             "adds a dict_match_score field (0-1, null if the word is OOV) to output."
    )
    return parser.parse_args()


def main():
    args = get_args()

    phon_dir = args.phonetic_dir
    w2v_dir = args.wav2vec_dir

    pron_dict = None
    if args.pronunciation_dict:
        dictionaries = [NSTLexiconDictionary.from_cleaned_json(p) for p in args.pronunciation_dict]
        pron_dict = dictionaries[0] if len(dictionaries) == 1 else CompositeDictionary(dictionaries)

    total = skipped_filter = skipped_no_file = emitted = 0
    dict_scores = []

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

                pairs = extract_pairs(
                    rec, phon_chunks, w2v_chunks,
                    start_tolerance=args.start_tolerance,
                    duration_tolerance=args.duration_tolerance,
                )
                for pair in pairs:
                    if args.no_epenthetic and pair.has_epenthetic:
                        continue
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
        msg = (
            f"\ntotal records: {total}  "
            f"skipped (filter): {skipped_filter}  "
            f"skipped (no file): {skipped_no_file}  "
            f"pairs emitted: {emitted}"
        )
        if pron_dict is not None:
            checked = len(dict_scores)
            avg = sum(dict_scores) / checked if checked else 0.0
            msg += f"  dict-checked: {checked}  avg dict_match_score: {avg:.3f}"
        print(msg, file=sys.stderr)


if __name__ == "__main__":
    main()
