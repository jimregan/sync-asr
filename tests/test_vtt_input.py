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
from sync_asr.vtt_input import VTTCaption, VTTInput
import os


can_run = True
try:
    from webvtt.structures import Caption
except ImportError:
    can_run = False


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_vtt_caption():
    if not can_run:
        return
    caption = Caption("00:01.000", "00:04.000", "Never drink liquid nitrogen.")
    vtt_caption = VTTCaption(caption)
    assert vtt_caption.start_time == 1000
    assert vtt_caption.end_time == 4000
    assert vtt_caption.text == "Never drink liquid nitrogen."


def test_vtt_input():
    if not can_run:
        return
    vtt_input = VTTInput(f"{TEST_DIR}/sample.vtt")
    assert len(vtt_input.captions) == 3
    assert vtt_input.captions[0].start_time == 1000
    assert vtt_input.captions[0].end_time == 4000
    assert vtt_input.captions[0].text == "Never drink liquid nitrogen."
    