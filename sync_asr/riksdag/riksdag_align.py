from .riksdag_api import RiksdagAPI, SpeakerElement
from ..ctm import CTMLine
from typing import List
from dataclasses import dataclass
from copy import deepcopy
from ..kaldi.align_ctm_ref import get_ctm_edits, smith_waterman_alignment
import string


@dataclass
class FilteredPair():
    ctmlines: List[CTMLine]
    riksdag_segments: SpeakerElement
    speaker_name: str = ""


# TODO: this assumes there is always a 'within' case
# which may not be true, in which case, breakage happens
def filter_ctm_with_riksdag(ctmlines, riksdag_output):
    within = False
    start = True

    last_i = i = j = 0
    pairs = []

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


def rd_similarity_score_function(x, y):
    left = x
    right = y.lower()
    while right[-1] in string.punctuation:
        right = right[:-1]

    if left == right:
        return 1
    return -1


def align_ctm_with_riksdag(pairs: List[FilteredPair],
                           similarity_score_function=None,
                           del_score=1, ins_score=1,
                           eps_symbol="<eps>", align_full_hyp=True):
    aligned_pairs = []

    for pair in pairs:
        if pair.riksdag_segments is not None:
            left_text = " ".join([t.text for t in pair.ctmlines])
            right_text = pair.riksdag_segments.text

    pass
