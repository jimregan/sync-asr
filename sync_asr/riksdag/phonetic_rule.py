# Copyright (c) 2023-2024, Jim O'Regan for Språkbanken Tal
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
import re
import itertools


_ALPHABET = {
    "A": ["a"],
    "B": ["be", "bé"],
    "C": ["ce", "se", "sé", "cé", "si", "ci"],
    "D": ["de", "dé", "di"],
    "E": ["e", "é"],
    "F": ["eff", "ef"],
    "G": ["ge", "gé", "gi"],
    "H": ["hå", "ho"],
    "I": ["i"],
    "J": ["ji", "gi"],
    "K": ["kå", "ko"],
    "L": ["ell", "el"],
    "M": ["emm", "em"],
    "N": ["enn", "en"],
    "O": ["o"],
    "P": ["pe", "pé", "pi"],
    "Q": ["qu"],
    "R": ["err", "er", "är", "ärr"],
    "S": ["ess", "es"],
    "T": ["te", "té", "ti"],
    "U": ["u"],
    "V": ["ve", "vé", "vi"],
    "W": ["dubbelve"],
    "X": ["ex", "ecz", "ecs", "eks"],
    "Y": ["y"],
    "Z": ["zäta", "säta", "seta", "zeta"],
    "Å": ["å"],
    "Ä": ["ä"],
    "Ö": ["ö"]
}

DIGITS = {
    "1": ["ett"],
    "2": ["två"],
    "3": ["tre"],
    "4": ["fyra"],
    "5": ["fem"],
    "6": ["sex"],
    "7": ["sju"],
    "8": ["åtta"],
    "9": ["nio", "ni"]
}


ALPHABET = {k: sorted(v, key=len, reverse=True) for k,v in _ALPHABET.items()}
ALNUM = {**ALPHABET, **DIGITS}
ALNUM_REGEX = {k: f"({'|'.join(v)})" for k,v in ALNUM.items()}
CONSONANTS = "bdfhjklmnprstvŋɕɖɡɧɭɳʂʈ"
VOWELS = "aeiouyøɪɑɔɛɵʉʊʏ"
ACCENTS = "²ˌˈ"


def shift_accent(ipa):
    accent = ""
    output = ""
    for character in ipa:
        if character in ACCENTS:
            accent = character
        elif character in CONSONANTS:
            output += character
        elif character in VOWELS:
            if accent != "":
                output += accent
                accent = ""
            output += character
        else:
            output += character
    return output


class Rule():
    def __init__(self, match, replacement, rulename, example, on_accented = False, before_accented = False):
        self.match = match
        self.replacement = replacement
        self.rulename = rulename
        self.example = example
        self.on_accented = on_accented
        self.before_accented = before_accented

    def apply(self, word):
        if self.on_accented:
            pattern = fr"((?:[^²ˌˈ]){self.match}|^{self.match})"
        elif self.before_accented:
            pattern = fr"({self.match}(?:[^²ˌˈ]))"
        else:
            word = re.sub("[²ˌˈ]", "", word)
            pattern = self.match
        matches = [(m.start(), m.end()) for m in re.finditer(pattern, word)]
        if self.on_accented:
            tmp = []
            for m in matches:
                if m[1] - m[0] > len(self.match):
                    tmp.append((m[1] - len(self.match), m[1]))
                else:
                    tmp.append(m)
            matches = tmp

        pieces = []
        prev_end = 0
        for piece in matches:
            if piece[0] > 0:
                pieces.append([word[prev_end:piece[0]]])
            pieces.append([word[piece[0]:piece[1]], self.replacement])
            prev_end = piece[1]
        pieces.append([word[prev_end:]])

        output = []
        for part in itertools.product(*pieces):
            output.append("".join(part))
        return output


class AssimilationRule(Rule):
    def __init__(self, match, replacement, rulename, example, on_accented = False, before_accented = False, pre_context = "", post_context = ""):
        super.__init__(match, replacement, rulename, example, on_accented, before_accented)
        self.pre_context = pre_context
        self.post_context = post_context


_GENERAL_STRESSED = [
    Rule("e", "ə", "e → ə / [-stressed]", "", True),
    Rule("ɛ", "ə", "e → ə / [-stressed]", "", True)
]

_ASSIMILATION = [
    AssimilationRule("r$", "", "h → ∅ / r # _", "har han", False, False, "", "h"),
    AssimilationRule("n$", "", "h → ∅ / n # _", "han har", False, False, "", "h"),
    AssimilationRule("r$", "", "r → ∅ / _ # [+consonant]", "där bilen", False, False, "", f"[{CONSONANTS}]")
]

Rule("[œɶeə]r", "r", "e → ∅ / _ r [+stressed]", "bero", False, True)
	
Rule("ɪntə", "ntə", "ɪ → ∅ / [+vowel] # _ n t ə", "ska inte", False, False)
Rule("ɪnte", "nte", "ɪ → ∅ / [+vowel] # _ n t e", "ska inte", False, False)

Rule("nh", "h", "n → ∅ / _ h", "Stenholm")