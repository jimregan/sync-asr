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
from sync_asr.hf_json_input import HuggingFaceJSON
import json


# https://en.wiktionary.org/wiki/File:En-au-sick_as_a_dog.ogg
# >>> input = "En-au-sick_as_a_dog.ogg"
# >>> from transformers import pipeline
# >>> model = "jonatasgrosman/wav2vec2-large-xlsr-53-english"
# >>> pipe = pipeline(model=model)
# >>> import json
# >>> json.dumps(output)
_SAMPLE = """
{
  "text": "sick as a dog",
  "chunks": [
    {
      "text": "sick",
      "timestamp": [
        0.28,
        0.46
      ]
    },
    {
      "text": "as",
      "timestamp": [
        0.52,
        0.58
      ]
    },
    {
      "text": "a",
      "timestamp": [
        0.66,
        0.68
      ]
    },
    {
      "text": "dog",
      "timestamp": [
        0.72,
        0.96
      ]
    }
  ]
}
"""


def test_huggingface_json():
    json_sample = json.loads(_SAMPLE)
    assert "chunks" in json_sample
    assert type(json_sample["chunks"]) == list
    assert len(json_sample["chunks"]) == 4
    hf_json = HuggingFaceJSON(data=json_sample)
    assert len(hf_json.words) == 4
    hf_json2 = HuggingFaceJSON(data=_SAMPLE)
    assert len(hf_json2.words) == 4
    assert hf_json.start_time == 280
    assert hf_json.end_time == 960