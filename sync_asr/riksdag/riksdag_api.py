import json
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
            pass

    def get_vidid(self):
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
        cur["speaker"] = speaker["text"]
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

