# Copyright (c) 2022, 2024 Jim O'Regan for Språkbanken Tal
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
from .elements import TimedWordSentence, TimedWord, TimedElement
from pathlib import Path
import json


class GentleWord(TimedWord):
    def __init__(self, start_time=0, end_time=0, text=0, aligned_word=None, case="", start_offset=0, end_offset=0, phones=[]):
        super().__init__(start_time, end_time, text)
        if aligned_word:
            self.aligned_word = aligned_word
        if case == "success":
            self.success = True
        else:
            self.success = False


class GentlePhone(TimedElement):
    def __init__(self, start_relative=0, duration=0, phone=""):
        super().__init__(start_relative, start_relative + duration, phone)


class GentleJSON(TimedWordSentence):
    def __init__(self, data=None, filename=""):
        if data is None and filename:
            words = self._load(filename)
            fileid = Path(filename).stem
        elif data is not None and filename == "":
            words = self._grab(data)
            fileid = None
        else:
            raise ValueError("GentleJSON requires exactly one of 'data' or 'filename' to be provided")
        super().__init__(words, fileid=fileid)

    def _load(self, filename):
        with open(filename) as jsonf:
            data = json.load(jsonf)
            if not "words" in data:
                raise ValueError(f"File {filename} does not appear to contain Gentle JSON")
            return self._grab(data, False)

    def _grab(self, data, warn=False):
        words = []
        if type(data) == str:
            data = json.loads(data)
        if not "words" in data or type(data["words"]) != list:
            raise ValueError(f"Data does not appear to contain Gentle JSON")
        for chunk in data["words"]:
            if warn:
                print(f'Reading word: {chunk.get("start")}:{chunk.get("end")} {chunk.get("word")}')
            words.append(GentleWord(start_time=float(chunk["start"]),
                                        end_time=int(chunk["end"]),
                                        text=chunk["word"]))
        return words
