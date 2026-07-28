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
import os
from unittest.mock import Mock, patch
from sync_asr.riksdag import RiksdagAPI2022 as ExportedRiksdagAPI2022
from sync_asr.riksdag import RiksdagAPI2026 as ExportedRiksdagAPI2026
from sync_asr.riksdag.riksdag_api import (
    RiksdagAPI,
    RiksdagAPI2022,
    RiksdagAPI2026,
    SpeakerElement,
    get_embedded_json,
)


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_versioned_api_exports():
    assert ExportedRiksdagAPI2022 is RiksdagAPI2022
    assert ExportedRiksdagAPI2026 is RiksdagAPI2026


def test_riksdag_api():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    assert "videodata" in rdapi.__dict__
    assert "streamurl" in rdapi.videodata
    assert isinstance(rdapi, RiksdagAPI2022)


def test_speaker_element():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    speakers = rdapi.videodata["speakers"]
    se = SpeakerElement(speakers[0])
    assert se.start_time == 14000
    assert se.duration == 233000
    assert se.speaker_name == "Ola Johansson"
    assert se.paragraphs[0].startswith("Herr talman! Det blir lite")
    assert se.text.startswith("Herr talman! Det blir lite")


def test_get_paragraphs_with_ids():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    pairs = rdapi.get_paragraphs_with_ids()
    assert pairs[0]["docid"] == "2442207160019927321_1_1"
    assert pairs[0]["text"].startswith("Herr talman!")


def test_get_speaker_elements():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    se = rdapi.get_speaker_elements()
    assert se[0].start_time == 14000
    assert se[0].duration == 233000
    assert se[0].speaker_name == "Ola Johansson"
    assert se[0].paragraphs[0].startswith("Herr talman! Det blir lite")
    assert se[0].text.startswith("Herr talman! Det blir lite")


def test_next_data():
    data = {
        "props": {"pageProps": {"contentApiData": {
            "documentId": "H001CU21",
            "title": "Nedsättning av en byggsanktionsavgift",
            "video": {
                "url": "https://example.test/2442207160019927321/playlist.m3u8",
                "duration": 252,
            },
            "speakers": [{
                "speaker": "Ola Johansson (C)",
                "party": "C",
                "startPosition": 14,
                "speechSeconds": 233,
                "speechNumber": 116,
                "speechText": "Herr talman!\r\nNästa stycke.",
            }],
        }}}
    }
    rdapi = RiksdagAPI2026(data=data)
    speaker = rdapi.get_speaker_elements()[0]
    assert rdapi.get_vidid() == "2442207160019927321"
    assert speaker.speaker_name == "Ola Johansson"
    assert speaker.start_time == 14000
    assert speaker.duration == 233000
    assert speaker.paragraphs == ["Herr talman!", "Nästa stycke."]


@patch("sync_asr.riksdag.riksdag_api.requests.get")
def test_get_embedded_json(mock_get):
    payload = {"props": {"pageProps": {"contentApiData": {}}}}
    response = Mock(content=(
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script>"
    ).encode())
    response.headers = {"content-type": "text/html"}
    mock_get.return_value = response
    assert get_embedded_json("https://example.test") == payload
    mock_get.assert_called_once_with("https://example.test", timeout=30)
    response.raise_for_status.assert_called_once_with()


def test_next_data_document_response():
    data = {"pageProps": {"contentApiData": {
        "document": {
            "debate": {"speeches": [{
                "debateId": "7C5FA450-E44D-43D1-82B2-260B9E1FDFC1",
                "debateTitle": "Skatt på bekämpningsmedel",
                "debateType": "Interpellationssvar",
                "documentId": "HD10462",
                "party": "M",
                "speaker": "Finansminister Elisabeth Svantesson (M)",
                "speechNumber": 8,
                "speechSeconds": 86,
                "speechText": "<p>Fru talman!</p><p>Andra stycket.</p>",
                "startPosition": 11,
            }]},
            "videos": [{
                "videoFileUrl": "https://example.test/2442606180056894521.smil/playlist.m3u8",
                "videoStatus": 2,
            }],
        },
    }}}
    rdapi = RiksdagAPI2026(data=data)
    speaker = rdapi.get_speaker_elements()[0]
    assert rdapi.get_vidid() == "7C5FA450-E44D-43D1-82B2-260B9E1FDFC1"
    assert rdapi.videodata["dokid"] == "HD10462"
    assert speaker.speaker_name == "Elisabeth Svantesson"
    assert speaker.start_time == 11000
    assert speaker.paragraphs == ["Fru talman!", "Andra stycket."]
