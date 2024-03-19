# Copyright (c) 2024, Jim O'Regan for Språkbanken Tal
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


class GeneaTSV(TimedWordSentence):
    def __init__(self, data=None, filename=""):
        if data is None:
            words, fileid = self._load(filename)
        elif filename == "":
            words = self._grab(data)
            fileid = None
        super().__init__(words, fileid=fileid)

    def _load(self, filename):
        fileid = Path(filename).stem
        lines = []
        with open(filename) as f:
            for line in f.readlines():
                lines.append(line.strip())
        words = self._grab(lines)
        return words, fileid

    def _grab(self, data, warn=False):
        words = []
        for line in data:
            parts = line.split("\t")
            words.append(TimedWord(start_time=int(float(parts[0]) * 1000),
                                        end_time=int(float(parts[1]) * 1000),
                                        text=parts[2]))
        return words
