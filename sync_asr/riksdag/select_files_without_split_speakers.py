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
from pathlib import Path
from .riksdag_api import RiksdagAPI, SpeakerElement


SPEAKERS = [
    "Jörgen Hellman",
    "Agneta Gille",
    "Amir Adan",
    "Teresa Carvalho",
    "Kerstin Nilsson",
    "Niclas Malmberg",
    "Carina Ståhl Herrstedt",
    "Vasiliki Tsouplaki",
    "Cecilie Tenfjord Toftby",
    "Ann-Britt Åsebol",
    "Karin Nilsson",
    "Ingemar Nilsson",
    "Mats Nordberg",
    "Ulrika Jörgensen",
    "Aylin Fazelian",
    "Björn Wiechel",
    "Sedat Dogru",
    "Oskar Öholm",
    "Eva Lohman",
    "Karin Granbom Ellison",
    "Åsa Karlsson",
    "Yilmaz Kerimo",
    "Aphram Melki",
    "Yasmine Bladelius",
    "Désirée Liljevall",
    "Erik Slottner",
    "Gustav Nilsson",
    "Linda Wemmert",
    "Mats Sander",
    "Arin Karapet",
    "Daniel Andersson",
    "David Josefsson",
]


def main():
    rdpath = Path("/Users/joregan/Playing/rdapi/api_output/")

    all_pairs = []
    for rdfile in rdpath.glob("*"):
        rdapi = RiksdagAPI(filename=str(rdfile))
        vidid = rdapi.get_vidid()
        if vidid is None or vidid == "":
            continue
        has_split_speaker = False
        for speaker in rdapi.get_speaker_elements():
            if speaker.speaker_name in SPEAKERS:
                has_split_speaker = True
        if not has_split_speaker:
            print(vidid)


if __name__ == '__main__':
    main()
