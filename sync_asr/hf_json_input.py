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
from .elements import TimedWordSentence, TimedWord
from pathlib import Path
import json


class HuggingFaceJSON(TimedWordSentence):
    def __init__(self, data=None, filename=""):
        if data is None:
            words = self._load(filename)
            fileid = Path(filename).stem
        elif filename == "":
            words = self._grab(data)
            fileid = None
        super().__init__(words, fileid=fileid)

    def _load(self, filename):
        with open(filename) as jsonf:
            data = json.load(jsonf)
            if not "chunks" in data:
                raise ValueError(f"File {filename} does not appear to contain HuggingFace JSON")
            return self._grab(data, False)

    def _grab(self, data, warn=False):
        words = []
        if type(data) == str:
            data = json.loads(data)
        if not "chunks" in data or type(data["chunks"]) != list:
            raise ValueError(f"Data does not appear to contain HuggingFace JSON")
        for chunk in data["chunks"]:
            if warn:
                print(f'Reading chunk: {chunk["timestamp"][0]}:{chunk["timestamp"][1]} {chunk["text"]}')
            words.append(TimedWord(start_time=int(chunk["timestamp"][0] * 1000),
                                        end_time=int(chunk["timestamp"][1] * 1000),
                                        text=chunk["text"]))
        return words
