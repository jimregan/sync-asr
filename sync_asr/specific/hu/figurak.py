# Copyright (c) 2024, Jim O'Regan
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
import requests

TEXT = "https://www.gutenberg.org/cache/epub/41683/pg41683.txt"
AUDIO = "https://ia803008.us.archive.org/16/items/multilingual_short_works_collection_010_1312_librivox/msw010_gizehipergamenlapok_gardonyi_dii_64kb.mp3"

START = "A gizehi pergamen-lapok."
END = "A nagyapó."

MODERNISATIONS = """
franczia francia
Bukfenczet Bukfencet
finánczokat fináncokat
arczomat, arcomat,
perczczel perccel
"""

NORMALISATIONS = """
1-ső	első
1-év,	első év,
3-ik	harmadik
3	három
5	öt
1879.	ezernyolcszázhetvenkilenc
126.	százhuszonhat
XL.	negyvenedik
§-a	paragrafusa
"""


JUNK = [
    "*",
    "* * *",
    "",
    " "
]


def get_raw_text():
    req = requests.get(TEXT)
    if req.status_code != 200:
        return ""
    the_text = START + req.text.split(START)[1].split(END)[0]
    # basic cleaning
    the_text = the_text.replace("_", "")
    return the_text


def get_paragraphs():
    the_text = get_raw_text()

    paragraphs = the_text.split("\r\n\r\n")
    paragraphs = [x.replace("\r\n", " ") for x in paragraphs if x not in JUNK]
    return paragraphs