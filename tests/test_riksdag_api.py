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
    #assert se.text.startswith("Herr talman! Det blir lite")