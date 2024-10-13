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


_CMU_ESPEAK_MAPPING = """
AA0 ɑː
AA1 ˈɑː
AA2 ˌɑː
AE0 æ
AE1 ˈæ
AE2 ˌæ
AH0 ə
AH0 ɐ
AH1 ˈʌ
AH2 ˌʌ
AO0 ɔː
AO1 ˈɔː
AO2 ˌɔː
AW0 aʊ
AW1 ˈaʊ
AW2 ˌaʊ
AY0 aɪ
AY1 ˈaɪ
AY2 ˌaɪ
B b
CH tʃ
D d
DH ð
EH0 ɛ
EH1 ˈɛ
EH2 ˌɛ
ER0 ɚ
ER1 ˈɜː
ER2 ˌɜː
EY0 eɪ
EY1 ˈeɪ
EY2 ˌeɪ
F f
G ɡ
HH h
IH0 ɪ
IH1 ˈɪ
IH2 ˌɪ
IY0 i
IY1 ˈiː
IY2 ˌiː
JH dʒ
K k
L l
M m
N n
NG ŋ
OW0 oʊ
OW1 ˈoʊ
OW2 ˌoʊ
OY0 ɔɪ
OY1 ˈɔɪ
OY2 ˌɔɪ
P p
R ɹ
S s
SH ʃ
T t
TH θ
UH0 ʊ
UH1 ˈʊ
UH2 ˌʊ
UW0 uː
UW1 ˈuː
UW2 ˌuː
V v
W w
Y j
Z z
ZH ʒ
"""


def cmudict_to_espeak_mapping(extended=False):
    MAPPING = _CMU_ESPEAK_MAPPING
    if extended:
        MAPPING += "\nDX ɾ"

    cmudict_to_espeak = {}
    for line in MAPPING.split("\n"):
        if line == "":
            continue
        line = line.strip()
        parts = line.split(" ")

        if len(parts) != 2:
            print(line)
            continue
        k, v = line.split(" ")
        if not k in cmudict_to_espeak:
            cmudict_to_espeak[k] = v

    return cmudict_to_espeak


# def espeakify(phlist, sep=""):
#     output = []
#     if phlist == ["spn"] or phlist == ["sil"]:
#         return ""
#     for phone in phlist:
#         if phone == "":
#             continue
#         if " " in phone:
#             output += [cmudict_to_espeak[x] for x in phone.split(" ")]
#         else:
#             output.append(cmudict_to_espeak[phone])
#     return sep.join(output)


