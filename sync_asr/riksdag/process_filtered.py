# Copyright (c) 2023, Jim O'Regan for Språkbanken Tal
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
from .filter_vtt_to_speaker_list import FilteredSegment, subsplit_segment_list

current = []
output = []
if __name__ == '__main__':
    with open("/Users/joregan/Playing/sync_asr/rdfilt-edit") as inf:
        for line in inf.readlines():
            line = line.strip()
            if line == "":
                if current == []:
                    continue
                output += subsplit_segment_list(current)
                current = []
            else:
                parts = line.split("\t")
                fs = FilteredSegment(parts[0], parts[1], parts[2], int(parts[3]), int(parts[4]), parts[5])
                current.append(fs)

    for res in output:
        print(res)
