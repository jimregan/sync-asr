# Copyright (c) 2024 Jim O'Regan for Språkbanken Tal
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
Aggregate per-chunk WER scores from metadata jsonl files to rank speakers
by ASR difficulty. Useful for selecting evaluation targets that stress-test
a pronunciation lexicon on non-standard phonology.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def read_metadata(paths, lang_prob_threshold):
    chunks = []
    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("is_silence", False):
                    continue
                if rec.get("lang_prob_sv", 1.0) < lang_prob_threshold:
                    continue
                if (rec.get("cer_whisper_first", 0.0) != 0.0
                        or rec.get("cer_whisper_last", 0.0) != 0.0
                        or rec.get("cer_wav2vec_first", 0.0) != 0.0
                        or rec.get("cer_wav2vec_last", 0.0) != 0.0):
                    continue
                if rec.get("wer_whisper") is None or rec.get("wer_wav2vec") is None:
                    continue
                chunks.append(rec)
    return chunks


def aggregate_by_speaker(chunks):
    speakers = defaultdict(lambda: {
        "wer_whisper": [],
        "wer_wav2vec": [],
        "name": None,
        "district": None,
        "party": None,
        "years": [],
    })

    for rec in chunks:
        sid = rec["speaker_id"]
        s = speakers[sid]
        s["wer_whisper"].append(rec["wer_whisper"])
        s["wer_wav2vec"].append(rec["wer_wav2vec"])
        if s["name"] is None:
            s["name"] = rec.get("name", "")
        if s["district"] is None:
            s["district"] = rec.get("district", "")
        if s["party"] is None:
            s["party"] = rec.get("party", "")
        year = rec.get("year")
        if year is not None:
            s["years"].append(year)

    results = []
    for sid, s in speakers.items():
        n = len(s["wer_whisper"])
        mean_whisper = sum(s["wer_whisper"]) / n
        mean_wav2vec = sum(s["wer_wav2vec"]) / n
        year_range = (
            f"{min(s['years'])}-{max(s['years'])}" if s["years"] else ""
        )
        results.append({
            "speaker_id": sid,
            "name": s["name"],
            "district": s["district"],
            "party": s["party"],
            "mean_wer_whisper": round(mean_whisper, 4),
            "mean_wer_wav2vec": round(mean_wav2vec, 4),
            "mean_wer_combined": round((mean_whisper + mean_wav2vec) / 2, 4),
            "chunk_count": n,
            "year_range": year_range,
        })

    return results


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", nargs="+", help="Metadata jsonl file(s)")
    parser.add_argument(
        "--min-chunks", type=int, default=10,
        help="Minimum number of usable chunks to include a speaker (default: 10)"
    )
    parser.add_argument(
        "--lang-prob", type=float, default=0.9,
        help="Minimum lang_prob_sv to accept a chunk (default: 0.9)"
    )
    parser.add_argument(
        "--top", type=int, default=None,
        help="Show only the N most difficult speakers"
    )
    parser.add_argument(
        "--sort-by", choices=["combined", "whisper", "wav2vec"], default="combined",
        help="Which WER to sort by (default: combined)"
    )
    parser.add_argument(
        "--tsv", action="store_true",
        help="Output as TSV instead of formatted table"
    )
    return parser.parse_args()


def main():
    args = get_args()

    paths = [Path(p) for p in args.jsonl]
    for p in paths:
        if not p.exists():
            print(f"Error: {p} does not exist", file=sys.stderr)
            sys.exit(1)

    chunks = read_metadata(paths, args.lang_prob)
    results = aggregate_by_speaker(chunks)

    results = [r for r in results if r["chunk_count"] >= args.min_chunks]

    sort_key = {
        "combined": "mean_wer_combined",
        "whisper": "mean_wer_whisper",
        "wav2vec": "mean_wer_wav2vec",
    }[args.sort_by]
    results.sort(key=lambda r: r[sort_key], reverse=True)

    if args.top:
        results = results[:args.top]

    if args.tsv:
        header = [
            "speaker_id", "name", "district", "party",
            "mean_wer_whisper", "mean_wer_wav2vec", "mean_wer_combined",
            "chunk_count", "year_range"
        ]
        print("\t".join(header))
        for r in results:
            print("\t".join(str(r[h]) for h in header))
    else:
        fmt = "{:<36}  {:<30}  {:<35}  {:>7}  {:>7}  {:>8}  {:>6}  {}"
        print(fmt.format(
            "speaker_id", "name", "district",
            "wer_wh", "wer_w2v", "combined", "chunks", "years"
        ))
        print("-" * 140)
        for r in results:
            print(fmt.format(
                r["speaker_id"],
                r["name"][:30],
                r["district"][:35],
                r["mean_wer_whisper"],
                r["mean_wer_wav2vec"],
                r["mean_wer_combined"],
                r["chunk_count"],
                r["year_range"],
            ))


if __name__ == "__main__":
    main()
