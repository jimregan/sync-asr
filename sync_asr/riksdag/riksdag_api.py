import json
from bs4 import BeautifulSoup
from pathlib import Path
import copy
import re


BASE_KEYS = [
    'videostatus', 'committee', 'type', 'debatepreamble', 'debatetexthtml',
    'livestreamurl', 'activelivespeaker', 'id', 'dokid', 'title',
    'debatename', 'debatedate', 'debatetype', 'debateurl', 'fromchamber',
    'thumbnailurl', 'debateseconds'
]


class RiksdagAPI():
    def __init__(self, data, filename="", verbose=False):
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

        if len(api_data["videodata"]) > 1:
            if verbose:
                print(f"More than one 'videodata' in {filename}")
            self.has_multiple_videodata = True


def _read_single_videodata(videodata, filename="", verbose=False, nullify=True):
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
        html = speaker["anftext"]
        soup = BeautifulSoup(html, 'html.parser')
        count = 1
        for para in soup.find_all("p"):
            if para.text.strip() == "":
                continue
            pg = copy.deepcopy(cur)
            pg["text"] = para.text
            pg["paragraph"] = count
            speakers.append(pg)
            count += 1
    base["speakers"] = speaker
    return base
        
