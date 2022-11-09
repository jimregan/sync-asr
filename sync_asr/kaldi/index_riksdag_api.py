import json
from bs4 import BeautifulSoup


BASE_KEYS = ['videostatus', 'committee', 'type', 'debatepreamble', 'debatetexthtml', 'livestreamurl', 'activelivespeaker', 'id', 'dokid', 'title', 'debatename', 'debatedate', 'debatetype', 'debateurl', 'fromchamber', 'thumbnailurl', 'debateseconds']
def read_api_json(filename):
    infile = str(filename)
    with open(infile) as input:
        data = json.load(input)
    assert "videodata" in data
    print(f"Reading {filename}")

    if len(data["videodata"]) > 1:
        print(f"More than one 'videodata' in {infile}")

    base = {}
    for key in BASE_KEYS:
        base[key] = data["videodata"][0][key]

    if not "streams" in data["videodata"][0] or data["videodata"][0]["streams"] is None:
        print(f"No 'streams' key found in {filename}")
        return None, None
    assert "streams" in data["videodata"][0]
    if not "files" in data["videodata"][0]["streams"] or data["videodata"][0]["streams"]["files"] is None:
        print(f"No 'files' key found in {filename}")
    assert "files" in data["videodata"][0]["streams"]
    if len(data["videodata"][0]["streams"]["files"]) > 1:
        print(f"More than one stream: {infile}")
    assert "url" in data["videodata"][0]["streams"]["files"][0]
    base["streamurl"] = data["videodata"][0]["streams"]["files"][0]["url"]


    if not "speakers" in data["videodata"][0] or data["videodata"][0]["speakers"] is None:
        print(f"No 'speakers' key found in {filename}")
        return None, None
    speakers = []
    for speaker in data["videodata"][0]["speakers"]:
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
            pg = cur
            pg["text"] = para.text
            pg["paragraph"] = count
            speakers.append(pg)
            count += 1
    return base, speakers