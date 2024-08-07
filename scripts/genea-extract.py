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
from sync_asr.ctm_edit import ctm_from_file, shift_epsilons
from pathlib import Path
FILLER1 = ["ah", "uh"]

def all_cor(lines):
    for line in lines:
        if line.edit != "cor":
            return False
    return True

for file in Path("/tmp/ctmedit").glob("*.ctmedit"):
    lines = ctm_from_file(str(file))
    edits_orig = {x: 0 for x in ["cor", "sub", "del", "ins"]}
    edits_post = {x: 0 for x in ["cor", "sub", "del", "ins"]}
    for line in lines:
        edits_orig[line.edit] += 1
        line.mark_correct_ignore_punct()
        edits_post[line.edit] += 1
    shifted = shift_epsilons(lines, epsilon="-")
    with open("/tmp/ctmedit2/" + file.name, "w") as of:
        for line in shifted:
            if line.edit != "cor" and line.text in FILLER1 and line.ref in FILLER1:
                line.set_correct_ref()
            of.write(str(line) + "\n")
    if all_cor(shifted):
        with open("/tmp/goodtext/" + file.name, "w") as of:
            of.write(" ".join([x.ref for x in shifted]) + "\n")

