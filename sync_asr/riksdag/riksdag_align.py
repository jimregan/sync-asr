# Copyright (c) 2022, Jim O'Regan for Språkbanken Tal
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
from .riksdag_api import RiksdagAPI, SpeakerElement
from ..ctm import CTMLine
from ..ctm_edit import CTMEditLine
from typing import List
from dataclasses import dataclass
from copy import deepcopy
from ..kaldi.align_ctm_ref import get_ctm_edits, smith_waterman_alignment
import string
import argparse
from .corrections import get_corrections
from pathlib import Path


@dataclass
class FilteredPair():
    ctmlines: List[CTMLine]
    riksdag_segments: SpeakerElement
    speaker_name: str = ""

    def ctm_words(self):
        return [t.text for t in self.ctmlines]

    def riksdag_words(self):
        return self.riksdag_segments.text.split()


def get_ctm_id_from_list(ctmlines):
    return ctmlines[0].id


def check_ctm_ids(ctmlines):
    base = ctmlines[0].id
    for line in ctmlines:
        if line.id != base:
            return False
    return True


def get_ctm_channel(ctmlines):
    return ctmlines[0].channel


def get_args():
    parser = argparse.ArgumentParser(description="""
    Align CTM with Riksdag API text
    """)
    # Arguments from align_ctm_ref.py
    parser.add_argument("--eps-symbol", type=str, default="-",
                        help="Symbol used to contain alignment "
                        "to empty symbol")
    parser.add_argument("--correct-score", type=int, default=1,
                        help="Score for correct matches")
    parser.add_argument("--substitution-penalty", type=int, default=1,
                        help="Penalty for substitution errors")
    parser.add_argument("--deletion-penalty", type=int, default=1,
                        help="Penalty for deletion errors")
    parser.add_argument("--insertion-penalty", type=int, default=1,
                        help="Penalty for insertion errors")
    parser.add_argument("ctm_path",
                        type=str,
                        default="",
                        help="""Path to location of CTM files.""")
    parser.add_argument("rdapi_in",
                        type=argparse.FileType('r'),
                        help="""Filename of Riksdag API file.""")
    args = parser.parse_args()
    return args


# TODO: this assumes there is always a 'within' case
# which may not be true, in which case, breakage happens
def filter_ctm_with_riksdag(ctmlines, rdapi):
    within = False
    start = True

    last_i = i = j = 0
    pairs = []

    riksdag_output = rdapi.get_speaker_elements()

    while (i < len(ctmlines) - 1) and (j < len(riksdag_output)):
        if (start or not within) and ctmlines[i].end_time < riksdag_output[j].start_time:
            i += 1
        elif within and ctmlines[i].end_time <= riksdag_output[j].end_time:
            i += 1
        else:
            if within:
                rd = riksdag_output[j]
                spkr = riksdag_output[j].text
                within = False
                j += 1
            else:
                if start:
                    start = False
                rd = None
                spkr = ""
                # check if we're not going straight into another within
                within = True
            pairs.append(FilteredPair(deepcopy(ctmlines[last_i:i]), rd, spkr))
            last_i = i
            i += 1
    if i < len(ctmlines):
        pairs.append(FilteredPair(deepcopy(ctmlines[last_i:-1]), None, ""))
    return pairs


def default_similarity_score_function(x, y):
    if x == y:
        return 1
    return -1


def rd_equals(x, y):
    left = x
    right = y.lower()
    corr = get_corrections()
    if len(right) > 1:
        while right[-1] in string.punctuation:
            right = right[:-1]
    if left == right:
        return True
    elif left in corr and corr[left] == right:
        return True
    return False


def rd_similarity_score_function(x, y):
    if rd_equals(x, y):
        return 1
    return -1


def align_ctm_with_riksdag(pairs: List[FilteredPair],
                           similarity_score_func=default_similarity_score_function,
                           del_score=-1, ins_score=-1,
                           eps_symbol="<eps>", align_full_hyp=True):
    aligned_pairs = []

    for pair in pairs:
        if pair.riksdag_segments is not None:
            ctm_words = pair.ctm_words()
            riksdag_words = pair.riksdag_words()
            output, score = smith_waterman_alignment(riksdag_words,
                                                     ctm_words,
                                                     similarity_score_func,
                                                     del_score, ins_score,
                                                     eps_symbol,
                                                     align_full_hyp)
            aligned_pairs.append((output, pair.ctmlines))
    return aligned_pairs


def run(args):
    del_score = -args.deletion_penalty
    ins_score = -args.insertion_penalty

    rdapi = RiksdagAPI(args.rdapi_in.read())
    if args.ctm_path == "":
        print("Path to CTM files empty")
        raise SystemExit(1)
    video_name = rdapi.get_vidid()
    ctm_path = Path(args.ctm_path)
    ctm_file = ctm_path / f"{video_name}.ctm"
    ctmlines = []
    with open(str(ctm_file)) as ctm_in:
        for line in ctm_in.readlines():
            ctmlines.append(CTMLine(line.strip()))

    pairs = filter_ctm_with_riksdag(ctmlines, rdapi)
    output = align_ctm_with_riksdag(pairs, rd_similarity_score_function, del_score=del_score, ins_score=ins_score)

    ctm_edits = []
    for pair in output:
        ctm_tmp = [p.ctm_list() for p in pair[1]]
        ctm_edits.append(get_ctm_edits(pair[0], ctm_tmp))

    if check_ctm_ids(pair[1]):
        ctm_id = get_ctm_id_from_list(pair[1])
        ctm_channel = get_ctm_channel(pair[1])
        for ctm_edit in ctm_edits:
            for line in ctm_edit:
                actual = [ctm_id, ctm_channel] + line
                ctm_edit = CTMEditLine(from_kaldi_list=actual)
                ctm_edit.mark_correct_from_function(rd_equals)
                print(ctm_edit)

def main():
    args = get_args()

    try:
        run(args)
    except Exception as e:
        print("Failed to align ref and hypotheses; "
              "got exception ", type(e), e)
        raise SystemExit(1)
    finally:
        # args.ctm_in.close()
        args.rdapi_in.close()


if __name__ == '__main__':
    main()
