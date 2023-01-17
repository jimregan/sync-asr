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
import os
from sync_asr.riksdag.riksdag_api import RiksdagAPI, SpeakerElement


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_riksdag_api():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    assert "videodata" in rdapi.__dict__
    assert "streamurl" in rdapi.videodata


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
