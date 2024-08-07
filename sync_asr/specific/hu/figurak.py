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

_MODERNISATIONS = """
franczia\tfrancia
Bukfenczet\tBukfencet
finánczokat\tfináncokat
arczomat,\tarcomat,
perczczel\tperccel
"""

_NORMALISATIONS = """
1-ső\telső
1-év,\telső év,
3-ik\tharmadik
13-ik\ttizenharmadik
3\thárom
5\töt
1879.\tezernyolcszázhetvenkilenc
126.\tszázhuszonhat
XL.\tnegyvenedik
§-a\tparagrafusa
t.-cz.\ttörvénycikk
"""


JUNK = [
    "*",
    "* * *",
    "",
    " "
]


def mkdict(multiline):
    output = {}
    for line in multiline.split("\n"):
        if line.strip() == "":
            continue
        parts = line.split("\t")
        assert len(parts) == 2, line
        output[parts[0]] = parts[1]
    return output


MODERNISATIONS = mkdict(_MODERNISATIONS)
NORMALISATIONS = mkdict(_NORMALISATIONS)


def _process_list(text, inlist):
    words = text.split(" ")
    output = []
    for word in words:
        if word in inlist:
            output.append(inlist[word])
        else:
            output.append(word)
    return " ".join(output)


def _process_list_maybe_mult(text, inlist):
    if type(text) == str:
        return _process_list(text, inlist)
    elif type(text) == list:
        output = []
        for line in text:
            output.append(_process_list(line, inlist))
        return output


def normalise(text):
    return _process_list_maybe_mult(text, NORMALISATIONS)


def modernise(text):
    return _process_list_maybe_mult(text, MODERNISATIONS)


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
