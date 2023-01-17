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
from .elements import TimedWord
from typing import List


class CTMLine(TimedWord):
    def __init__(self, from_line=""):
        self.from_line(from_line)
        start_time = self.start_time
        end_time = self.end_time
        text = self.text
        super().__init__(start_time, end_time, text)

    def __str__(self) -> str:
        return " ".join(self.as_list())

    def __repr__(self) -> str:
        return f"{self.id} ({self.start_time, self.end_time}) {self.text}"

    def from_line(self, text: str):
        """
        Reads a single CTM line:

        AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0

        :param text: the string to read from
        """
        parts = text.strip().split()
        self.id = parts[0]
        self.channel = parts[1]
        self.start_time = int(float(parts[2]) * 1000)
        self.duration = int(float(parts[3]) * 1000)
        self.end_time = self.start_time + self.duration
        self.text = parts[4]
        self.confidence = float(parts[5])

    def as_list(self):
        """
        returns a list containing the pieces of a CTM line, for use in
        other processing. Makes start_time and duration into fractions
        of a second, instead of milliseconds.
        """
        return [
            self.id,
            self.channel,
            str(float(self.start_time / 1000)),
            str(float(self.duration / 1000)),
            self.text,
            str(self.confidence),
        ]
    
    def ctm_list(self):
        """
        returns a list suitable for plugging into get_ctm_edits
        """
        return [
            float(self.start_time / 1000),
            float(self.duration / 1000),
            self.text,
            self.confidence,
        ]
    
    def ctm_text(self):
        return " ".join(self.as_list())


def ctm_from_file(filename):
    ctm_lines = []
    with open(filename) as input:
        for line in input.readlines():
            ctm_lines.append(CTMLine(line.strip()))
    return ctm_lines


def ctm_list_to_lines(ctmlines: List[CTMLine]) -> List[str]:
    return [c.ctm_text() for c in ctmlines]
