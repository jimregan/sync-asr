from .riksdag_api import RiksdagAPI, SpeakerElement
from ..ctm import CTMLine
from typing import List
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class FilteredPair():
    ctmlines: List[CTMLine]
    riksdag_segments: List[SpeakerElement]
    speaker_name: str = ""


def filter_ctm_with_riksdag(ctmlines, riksdag_output):
    ctm_i = 0
    rd_i = 0

    pairs = []
    cur = []

    # for i in ctmlines
    #  for j in rd:
    #   if i < first rd line:
    #     add to 
    while rd_i < len(riksdag_output):
        while ctm_i < len(ctmlines):
            if ctmlines[ctm_i].end_time < riksdag_output[rd_i].start_time:
                cur.append(ctmlines[ctm_i])
            else:
                if rd_i == 0:
                    cur_pair = FilteredPair(deepcopy(cur), None)
                #elif 
                else:
                    pass
                pairs.append(cur_pair)
                cur = []
                rd_i += 1

