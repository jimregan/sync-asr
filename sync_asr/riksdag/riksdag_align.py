from .riksdag_api import RiksdagAPI, SpeakerElement
from ..ctm import CTMLine
from typing import List
from dataclasses import dataclass


@dataclass
class FilteredPair():
    ctmlines: List[CTMLine]
    riksdag_segments: List[SpeakerElement]
    speaker_name: str = ""
    is_unaligned: bool = False


def filter_ctm_with_riksdag(ctmlines, riksdag_output):
    ctm_i = 0
    rd_i = 0

    murmur_lines = []

    pairs = []

    # the 'murmur' lines collected here will need to be further
    # filtered, because there will typically be untranscribed
    # speech for speaker introductions, etc.
    # Further processing will be required
    while ctmlines[ctm_i] < riksdag_output[0]:
        murmur_lines.append(ctmlines[ctm_i])
        ctm_i += 1

