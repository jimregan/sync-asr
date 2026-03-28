# Copyright (c) 2024 Jim O'Regan for Språkbanken Tal
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
from sync_asr.whisperx_json_input import WhisperXJSON, WhisperXWord
import json


# Typical WhisperX output after word-level alignment (no diarisation)
_SAMPLE = """
{
  "segments": [
    {
      "start": 0.28,
      "end": 0.96,
      "text": " sick as a dog",
      "words": [
        {"word": "sick", "start": 0.28, "end": 0.46, "score": 0.95},
        {"word": "as",   "start": 0.52, "end": 0.58, "score": 0.99},
        {"word": "a",    "start": 0.66, "end": 0.68, "score": 0.99},
        {"word": "dog",  "start": 0.72, "end": 0.96, "score": 0.97}
      ]
    }
  ]
}
"""

# WhisperX output after diarisation — speaker may be on segment or word
_SAMPLE_WITH_SPEAKER = """
{
  "segments": [
    {
      "start": 0.28,
      "end": 0.96,
      "text": " sick as a dog",
      "speaker": "SPEAKER_00",
      "words": [
        {"word": "sick", "start": 0.28, "end": 0.46, "score": 0.95, "speaker": "SPEAKER_00"},
        {"word": "as",   "start": 0.52, "end": 0.58, "score": 0.99, "speaker": "SPEAKER_00"},
        {"word": "a",    "start": 0.66, "end": 0.68, "score": 0.99, "speaker": "SPEAKER_00"},
        {"word": "dog",  "start": 0.72, "end": 0.96, "score": 0.97, "speaker": "SPEAKER_00"}
      ]
    }
  ]
}
"""

# WhisperX sometimes omits end time for the last word in a segment
_SAMPLE_MISSING_END = """
{
  "segments": [
    {
      "start": 0.28,
      "end": 0.96,
      "text": " sick as a dog",
      "words": [
        {"word": "sick", "start": 0.28, "end": 0.46, "score": 0.95},
        {"word": "as",   "start": 0.52, "end": 0.58, "score": 0.99},
        {"word": "a",    "start": 0.66, "end": 0.68, "score": 0.99},
        {"word": "dog",  "start": 0.72, "end": null,  "score": 0.97}
      ]
    }
  ]
}
"""


def test_whisperx_json():
    data = json.loads(_SAMPLE)
    wx = WhisperXJSON(data=data)
    assert len(wx.words) == 4
    assert wx.start_time == 280
    assert wx.end_time == 960


def test_whisperx_json_string():
    wx = WhisperXJSON(data=_SAMPLE)
    assert len(wx.words) == 4


def test_whisperx_json_speaker_on_segment():
    data = json.loads(_SAMPLE_WITH_SPEAKER)
    wx = WhisperXJSON(data=data)
    assert len(wx.words) == 4
    assert all(w.speaker == "SPEAKER_00" for w in wx.words)


def test_whisperx_json_missing_end_skipped():
    data = json.loads(_SAMPLE_MISSING_END)
    wx = WhisperXJSON(data=data)
    assert len(wx.words) == 3


def test_whisperx_word_has_speaker():
    w = WhisperXWord(start_time=280, end_time=460, text="sick", speaker="SPEAKER_00")
    assert w.speaker == "SPEAKER_00"
    assert w.text == "sick"
