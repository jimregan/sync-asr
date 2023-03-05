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
import sys


MIN_ALIGNED = 3.0

lines = []
with open(sys.argv[1]) as ctmin:
    for line in ctmin.readlines():
        lines.append(line.strip().split(" "))

merged = []
current = []
last_was_cor = False
for line in lines:
    is_cor = line[7] == "cor"
    if is_cor == last_was_cor:
        current.append(line)
    else:
        if current != []:
            merged.append(current)
        current = []
        current.append(line)
        last_was_cor = not last_was_cor
merged.append(current)

print("FILE\tSTART\tEND\tLABEL\tTEXT")
for merge in merged:
    start = float(merge[0][2])
    end = float(merge[-1][2]) + float(merge[-1][3])
    text = " ".join(x[6] for x in merge)
    o_text = " ".join(x[4] for x in merge)
    o_text = o_text.replace("<eps>", "")
    o_text = o_text.replace("  ", " ")
    if merge[0][7] == "cor":
        # text = " ".join(x[6] for x in merge)
        op = "ALIGNED"
    else:
        text = text.replace("<eps>", "")
        text = text.replace("  ", " ")
        text = f'{o_text + " | " + text}'
        text = ""
        op = "MISALIGNED"
    if (end - start) > MIN_ALIGNED:
        print(f"{merge[0][0]}\t{start}\t{end}\t{op}\t{text}")
