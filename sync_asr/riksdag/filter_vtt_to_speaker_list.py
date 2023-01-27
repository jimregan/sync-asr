# Copyright (c) 2023, Jim O'Regan for Språkbanken Tal
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
# 
# This file is to extract a set of captions from Whisper's output
# based on speaker information from the Riksdag API, for a fixed
# set of speakers (the test/validation set)
# 
# This file is temporary, and will be deleted after there's a
# public release.
from .riksdag_api import RiksdagAPI, SpeakerElement
from ..vtt_input import VTTInput, VTTCaption
from typing import List
from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path
import argparse


TEST_M = [
    'Ingemar Nilsson',
    'Amir Adan',
    'Per Bill',
    'Mats Nordberg',
    'Jörgen Hellman',
    'Oskar Öholm',
    'Lars Jilmstad',
    'Aphram Melki'
]

VAL_M = [
    'Magnus Sjödahl',
    'Mats Sander',
    'Sedat Dogru',
    'Erik Slottner',
    'Gustav Nilsson',
    'Björn Wiechel',
    'Yilmaz Kerimo',
    'Niclas Malmberg'
]

TEST_F = [
    'Yasmine Bladelius',
    'Karin Granbom Ellison',
    'Carina Ståhl Herrstedt',
    'Ann-Britt Åsebol',
    'Linda Wemmert',
    'Ulrika Jörgensen',
    'Teresa Carvalho',
    'Karin Nilsson'
]

VAL_F = [
    'Åsa Karlsson',
    'Eva Lohman',
    'Désirée Liljevall',
    'Cecilie Tenfjord Toftby',
    'Aylin Fazelian',
    'Agneta Gille',
    'Kerstin Nilsson',
    'Vasiliki Tsouplaki'
]

ALL_SPEAKERS = list(set(TEST_F + TEST_M + VAL_M + VAL_F))


@dataclass
class FilteredPair():
    vttlines: List[VTTCaption]
    riksdag_segments: SpeakerElement
    speaker_name: str = ""
    vidid: str = ""

    def vtt_words(self):
        return [t.text.split() for t in self.vttlines]

    def riksdag_words(self):
        return self.riksdag_segments.text.split()

    def vtt_text(self):
        return [t.text for t in self.vttlines]

    def riksdag_text(self):
        return self.riksdag_segments.text

    def get_set(self):
        if self.speaker_name in TEST_F:
            return "TEST_F"
        elif self.speaker_name in TEST_M:
            return "TEST_M"
        elif self.speaker_name in VAL_F:
            return "VAL_F"
        elif self.speaker_name in VAL_M:
            return "VAL_M"


# TODO: this assumes there is always a 'within' case
# which may not be true, in which case, breakage happens
def filter_vtt_with_riksdag(vttcaptions, rdapi, vidid):
    within = False
    start = True

    last_i = i = j = 0
    pairs = []

    riksdag_output = rdapi.get_speaker_elements()
    filtered = []
    for rdo in riksdag_output:
        if rdo.speaker_name in ALL_SPEAKERS:
            filtered.append(deepcopy(rdo))
    riksdag_output = filtered
    if len(riksdag_output) == 0:
        return []

    while (i < len(vttcaptions) - 1) and (j < len(riksdag_output)):
        if (start or not within) and vttcaptions[i].end_time < riksdag_output[j].start_time:
            i += 1
        elif within and vttcaptions[i].end_time <= riksdag_output[j].end_time:
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
            pairs.append(FilteredPair(deepcopy(vttcaptions[last_i:i]), rd, spkr, vidid))
            last_i = i
            i += 1
    if i < len(vttcaptions):
        pairs.append(FilteredPair(deepcopy(vttcaptions[last_i:-1]), None, "", vidid))
    return pairs


def get_args():
    parser = argparse.ArgumentParser(description="""
    Filter Whisper CTMs by a (hardcoded) speaker list
    """)
    parser.add_argument("--insertion-penalty", type=int, default=1,
                        help="Penalty for insertion errors")
    parser.add_argument("vtt_path",
                        type=str,
                        help="Path to VTT files")
    parser.add_argument("rdapi_path",
                        type=str,
                        help="Path to Riksdag API files.")
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    rdpath = Path(args.rdapi_path)
    VTT_PATH = Path(args.vtt_path)
    if not rdpath.is_dir():
        print("Expected a directory", args.rdapi_path)
    if not VTT_PATH.is_dir():
        print("Expected a directory", args.vtt_path)

    all_pairs = []
    for rdfile in rdpath.glob("*"):
        rdapi = RiksdagAPI(filename=str(rdfile))
        vidid = rdapi.get_vidid()
        if vidid is None or vidid == "":
            print("Error opening file", str(rdfile))
            continue
        has_sought_speaker = False
        for speaker in rdapi.get_speaker_elements():
            if speaker.speaker_name in ALL_SPEAKERS:
                has_sought_speaker = True
        if not has_sought_speaker:
            print("No sought speakers", str(rdfile))
            continue
        vtt_path = VTT_PATH / f"{vidid}_480p.mp4.vtt"
        if not vtt_path.exists():
            print("VTT file does not exist", str(vtt_path))
        vtt = VTTInput(str(vtt_path))
        pairs = filter_vtt_with_riksdag(vtt.captions, rdapi, vidid)
        all_pairs += pairs


if __name__ == '__main__':
    main()
