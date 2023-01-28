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


@dataclass
class FilteredSegment():
    name: str
    set_name: str
    vidid: str
    start: int
    end: int
    text: str

    def __str__(self):
        return f"{self.name}\t{self.set_name}\t{self.vidid}\t{str(self.start)}\t{str(self.end)}\t{self.text}"


def subsplit_segment_list(segments):
    two_minutes = (2 * 60 * 1000)

    close_enough = two_minutes + 5000

    running_total = 0
    start = segments[0].start

    output = []
    def merge(a, b, text):
        start = a.start
        end = b.end
        new = FilteredSegment(a.name, a.set_name, a.vidid, start, end, text)
        return new

    i = 0
    if (segments[-1].end - segments[0].start) > two_minutes:
        for i in range(1, len(segments)):
            cur_total = segments[i].end - start
            if cur_total > close_enough and running_total > two_minutes:
                index = i - 1
                text = " ".join(x.text for x in segments[0:index])
                output.append(merge(segments[0], segments[index], text))
                break
            running_total = cur_total
    running_total = 0
    if (segments[-1].end - segments[i].start) > two_minutes:
        j = i
        start = segments[j].start
        for i in range(j + 1, len(segments)):
            cur_total = segments[i].end - start
            if cur_total > close_enough and running_total > two_minutes:
                index = i - 1
                text = " ".join(x.text for x in segments[j:index])
                output.append(merge(segments[j], segments[index], text))
                break
            running_total = cur_total

    return output


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
                spkr = riksdag_output[j].speaker_name
                within = False
                j += 1
            else:
                if start:
                    start = False
                rd = None
                spkr = ""
                # check if we're not going straight into another within
                within = True
            if rd is not None and spkr != "":
                pairs.append(FilteredPair(deepcopy(vttcaptions[last_i:i]), rd, spkr, vidid))
            last_i = i
            i += 1
    # if i < len(vttcaptions):
    #     pairs.append(FilteredPair(deepcopy(vttcaptions[last_i:-1]), None, "", vidid))
    return pairs


def get_args():
    parser = argparse.ArgumentParser(description="""
    Filter Whisper CTMs by a (hardcoded) speaker list
    """)
    parser.add_argument("vtt_path",
                        type=str,
                        help="Path to VTT files")
    parser.add_argument("rdapi_path",
                        type=str,
                        help="Path to Riksdag API files.")
    args = parser.parse_args()
    return args


def split_point(seg1, seg2, duration = 3000):
    if seg1.name != seg2.name:
        return True
    elif seg1.vidid != seg2.vidid:
        return True
    elif (seg2.start - seg1.end) > duration:
        return True
    else:
        return False


def partition_segments(segments):
    segmented = []
    current = []

    for i, j in zip(range(0, len(segments)-1), range(1, len(segments))):
        if split_point(segments[i], segments[j]):
            current.append(segments[i])
            segmented.append(deepcopy(current))
            current = []
        else:
            current.append(segments[i])
        i += 1
        j += 1
    return segmented


def filter_segmented(segmented):
    for seg in segmented:
        if len(seg) > 2 and seg[1].text.startswith("Tack"):
            seg = seg[1:]


def is_usable_segment(segments):
    min_time = 4 * 60 * 1000
    return (segments[-1].end - segments[0].start) < min_time


def main():
    verbose = False
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
            if verbose:
                print("Error opening file", str(rdfile))
            continue
        has_sought_speaker = False
        for speaker in rdapi.get_speaker_elements():
            if speaker.speaker_name in ALL_SPEAKERS:
                has_sought_speaker = True
        if not has_sought_speaker and verbose:
            print("No sought speakers", str(rdfile))
            continue
        vtt_path = VTT_PATH / f"{vidid}_480p.mp4.vtt"
        if not vtt_path.exists():
            if verbose:
                print("VTT file does not exist", str(vtt_path))
            continue
        vtt = VTTInput(str(vtt_path))
        pairs = filter_vtt_with_riksdag(vtt.captions, rdapi, vidid)
        all_pairs += pairs

    filtered_segments = []
    for pair in all_pairs:
        for caption in pair.vttlines:
            fs = FilteredSegment(pair.speaker_name, pair.get_set(), pair.vidid, caption.start_time, caption.end_time, caption.text.strip())
            filtered_segments.append(fs)

    for ps in partition_segments(filtered_segments):
        for ss in ps:
            print(ss)
        print("\n")

if __name__ == '__main__':
    main()
