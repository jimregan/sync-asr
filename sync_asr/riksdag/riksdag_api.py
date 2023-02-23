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
import json
from typing import Tuple
from bs4 import BeautifulSoup
import copy
import re
from sync_asr.elements import TimedElement


BASE_KEYS = [
    'videostatus', 'committee', 'type', 'debatepreamble', 'debatetexthtml',
    'livestreamurl', 'activelivespeaker', 'id', 'dokid', 'title',
    'debatename', 'debatedate', 'debatetype', 'debateurl', 'fromchamber',
    'thumbnailurl', 'debateseconds'
]


TITULAR = """
Arbetsm.- och etableringsmin.
Arbetsmarknads- och jämställdhetsminister
Arbetsmarknadsminister
Finansminister
Försvarsminister
Infrastrukturminister
Justitie- och inrikesminister
Justitie- och migrationsmin.
Justitie- och migrationsminister
Justitieminister
Klimat- och miljöminister
Kultur- och demokratiminister
Kultur- och idrottsminister
Kulturminister
Landsbygdsminister
Miljö- och klimatminister
Miljöminister
Näringsminister
Närings- och innovationsmin.
Socialförsäkringsminister
Socialminister
Statsminister
Statsrådet
Utbildningsminister
Utrikesminister
""".split("\n")
TITULAR = [x for x in TITULAR if x != ""]


def split_title(text: str) -> Tuple[str, str]:
    for title in TITULAR:
        if text.startswith(title.strip()):
            return (title, text[len(title) :].strip())
    return ("", text)


class SpeakerElement(TimedElement):
    def __init__(self, speaker):
        self.speaker_name = speaker["speaker"]
        self.start_time = int(speaker["start"] * 1000)
        self.duration = int(speaker["duration"] * 1000)
        self.end_time = self.start_time + self.duration
        self.text = " ".join(p for p in speaker["paragraphs"])
        self.paragraphs = speaker["paragraphs"]
        super().__init__(self.start_time, self.end_time, self.text)


class RiksdagAPI():
    def __init__(self, data=None, filename="", verbose=False, nullify=False):
        api_data = data
        if data is None:
            with open(filename) as fp:
                api_data = json.load(fp)

        if type(data) == str:
            api_data = json.loads(data)

        if filename != "":
            if verbose:
                print(f"Reading data from {filename}")

        if not "videodata" in api_data:
            raise ValueError("Data does not appear to contain Riksdag API output")

        video_data_tmp = []
        for videodata in api_data["videodata"]:
            video_data_tmp.append(read_videodata(videodata, filename, verbose, nullify))
        if len(video_data_tmp) == 1:
            self.videodata = video_data_tmp[0]
        else:
            self.videodata = video_data_tmp

    def get_speaker_elements(self):
        if type(self.videodata) == list:
            viddata = self.videodata
        else:
            viddata = [self.videodata]
        output = []
        for vd in viddata:
            if "speakers" in vd:
                for speaker in vd["speakers"]:
                    output.append(SpeakerElement(speaker))
        return output

    def get_vidid(self):
        if not "streamurl" in self.videodata:
            return None
        base = self.videodata["streamurl"]
        if "/" in base:
            parts = base.split("/")
            return parts[-1]
        else:
            return base

    def get_paragraphs_with_ids(self):
        if type(self.videodata) == list:
            viddata = self.videodata
        else:
            viddata = [self.videodata]
        output = []
        for vd in viddata:
            speaker_turn = 1
            for speaker in vd["speakers"]:
                paragraph_num = 1
                for paragraph in speaker["paragraphs"]:
                    docid = f'{self.get_vidid()}_{speaker_turn}_{paragraph_num}'
                    output.append({"docid": docid, "text": paragraph})
                    paragraph_num += 1
                speaker_turn += 1
        return output


def read_videodata(videodata, filename="", verbose=False, nullify=True):
    base = {}
    for key in BASE_KEYS:
        base[key] = videodata[key]

    input_name = filename
    if input_name == "":
        input_name = "data"

    if not "streams" in videodata or videodata["streams"] is None:
        if verbose:
            print(f"No 'streams' key found in {input_name}")
        if nullify:
            return None
        else:
            return base

    if not "files" in videodata["streams"] or videodata["streams"]["files"] is None:
        if verbose:
            print(f"No 'files' key found in {input_name}")

    if len(videodata["streams"]["files"]) > 1:
        if verbose:
            print(f"More than one stream: {input_name}")
        base["streamurls"] = [x["url"] for x in videodata["streams"]["files"] if "url" in x]

    if "url" in videodata["streams"]["files"][0]:
        base["streamurl"] = videodata["streams"]["files"][0]["url"]

    if not "speakers" in videodata or videodata["speakers"] is None:
        if verbose:
            print(f"No 'speakers' key found in {input_name}")
        if nullify:
            return None
        else:
            return base

    speakers = []
    for speaker in videodata["speakers"]:
        cur = {}
        for key in ["start", "duration", "party", "subid", "active", "number"]:
            cur[key] = speaker[key]
        cur["speaker_text"] = speaker["text"]
        cur["speaker"] = speaker["text"]
        st = split_title(cur["speaker"])
        tmptitle, tmptext = st[0], st[1]
        if tmptitle != "":
            cur["title"] = tmptitle
            cur["speaker"] = tmptext
        ending = f" ({cur['party']})"
        if cur["speaker"].endswith(ending):
            cur["speaker"] = cur["speaker"][:-len(ending)]
        cur["paragraphs"] = get_speaker_paragraphs(speaker["anftext"])
        speakers.append(copy.deepcopy(cur))
    base["speakers"] = speakers
    return base


def get_speaker_paragraphs(html):
    if "<p>" in html or "<P>" in html:
        soup = BeautifulSoup(html, 'html.parser')
        paragraphs = []
        for para in soup.find_all("p"):
            if para.text.strip() != "" and not para.text.strip().startswith("STYLEREF Kantrubrik"):
                paragraphs.append(para.text.strip())
        return paragraphs
    else:
        text = html.strip().replace("\r\n", "\n").replace("\r", "\n")
        return text.split("\n")


PUNCT_FINAL = [")", ".", ",", "!", ":", ";", "?", '"']


def clean_text(text):
    text = text.strip().replace("\r\n", " ")
    if text == "":
        return ""
    if len(text) == 1 and text in PUNCT_FINAL:
        return ""
    while text[-1] in PUNCT_FINAL:
        text = text[:-1]
    while text[0] in ["(", '"']:
        text = text[1:]
    text = text.replace("\n", " ")
    text = text.strip()
    text = text.replace('"', "")
    text = text.replace(". ", " ")
    text = text.replace(", ", " ")
    text = text.replace(";", "")
    text = text.replace(": ", " ")
    text = text.replace("!", "")
    text = text.replace("?", "")
    text = re.sub("  +", " ", text)
    text = text.lower()
    return text

