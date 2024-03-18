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
import copy
from string import punctuation


def clean_text(work_ref, PUNCT, lower=True):
    i = 0
    l = len(work_ref)
    while i < l and work_ref[i] in PUNCT:
        i += 1
    j = -1
    while j >= -l and work_ref[j] in PUNCT:
        j -= 1
    retval = work_ref[i:j+1]
    if lower:
        retval = retval.lower()
    return retval


def _approx_match(texta, textb):
    punct = set(punctuation)
    return texta == clean_text(textb, punct)


def possible_false_start(text, ref, fillers=[], mark_filler=False):
    punct = set(punctuation)
    clean = clean_text(ref, punct)
    if text.endswith(clean):
        fs = text[:-len(clean)]
        if fs in fillers:
            if mark_filler:
                return f"[{fs}]_{ref}"
            else:
                return f"{fs}-_{ref}"
        elif clean.startswith(fs):
            return f"{fs}-_{ref}"
        else:
            return None
    else:
        return None


class CTMEditLine(TimedWord):
    def __init__(self, from_line="", from_kaldi_list=None, verbose=False):
        if from_line != "":
            self.from_line(from_line)
        elif from_kaldi_list is not None:
            self.from_list(from_kaldi_list, True)
        start_time = self.start_time
        end_time = self.end_time
        text = self.text
        super().__init__(start_time, end_time, text)
        self.verbose = verbose
        self.PUNCT = set(punctuation)

    def __str__(self) -> str:
        return " ".join(self.as_list())

    def __repr__(self) -> str:
        return f"{self.id} ({self.start_time, self.end_time}) {self.text}|{self.ref}"
    
    def __eq__(self, other):
        return self.id == other.id and \
               self.start_time == other.start_time and \
               self.end_time == other.end_time and \
               self.text == other.text and \
               self.ref == other.ref and \
               self.edit == other.edit

    def from_line(self, text: str):
        # AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil tainted
        parts = text.strip().split()
        self.from_list(parts, False)

    def from_list(self, parts, kaldi_list=False):
        EDITS = ["cor", "ins", "del", "sub", "sil"]
        self.id = parts[0]
        self.channel = parts[1]
        if kaldi_list:
            self.start_time = int(parts[2] * 1000)
            self.duration = int(parts[3] * 1000)
        else:
            self.start_time = int(float(parts[2]) * 1000)
            self.duration = int(float(parts[3]) * 1000)
        self.end_time = self.start_time + self.duration
        self.text = parts[4]
        if kaldi_list:
            self.confidence = parts[5]
        else:
            self.confidence = float(parts[5])
        self.ref = parts[6]
        if parts[7] in EDITS:
            self.edit = parts[7]
        else:
            raise ValueError(f"Unknown edit type: {parts[7]}")
        if len(parts) >= 9:
            if parts[8] == "tainted":
                self.tainted = True
        # Extension to the format
        if len(parts) > 8 and ":" in parts[-1]:
            self.props = { k:v for k,v in (p.split(":") for p in parts[-1].split(";")) }

    def as_list(self):
        out = [
            self.id,
            self.channel,
            str(float(self.start_time / 1000)),
            str(float(self.duration / 1000)),
            self.text,
            str(self.confidence),
            self.ref,
            self.edit, 
        ]
        if "tainted" in self.__dict__ and self.tainted:
            out.append("tainted")
        if "props" in self.__dict__ and self.props:
            out.append(";".join([f"{a[0]}:{a[1]}" for a in self.props.items()]))
        return out
    
    def mark_correct_from_list(self, collisions, case_punct=False, make_equal=True):
        def checksout(ref, col):
            return ((type(col) == str and ref == col) or \
                (type(col) == list and ref in col))
        work_ref = self.ref
        if case_punct:
            work_ref = clean_text(self.ref, self.PUNCT)
        if self.text in collisions:
            orig_text = self.text
            collision = collisions[self.text]
            if checksout(work_ref, collision):
                if make_equal:
                    self.text = self.ref
                self.edit = "cor"
                if self.verbose:
                    self.set_prop("collision", f"{orig_text}_{work_ref}")

    def mark_correct_from_function(self, comparison_function, make_equal=True):
        if comparison_function(self.text, self.ref):
            self.edit = "cor"
            if make_equal:
                self.text = self.ref        

    def check_filler_or_false_starts(self, fillers=[], mark_filler=True):
        pfs = possible_false_start(self.text, self.ref, fillers, mark_filler)
        if pfs is not None:
            self.text = self.ref = pfs
            self.edit = "cor"

    def set_correct_ref(self):
        self.text = self.ref
        self.edit = "cor"

    def set_correct_text(self):
        self.ref = self.text
        self.edit = "cor"

    def fix_case_difference(self):
        comp = clean_text(self.ref, self.PUNCT)
        if self.text == comp:
            self.set_correct_ref()

    def has_props(self):
        return "props" in self.__dict__

    def set_prop(self, key, value):
        if not self.has_props():
            self.props = {}
        self.props[key] = value

    def delete_props(self):
        if self.has_props():
            del self.props

    def get_prop(self, key):
        if self.has_props():
            return self.props[key]
        else:
            return None

    def has_eps(self, eps="<eps>"):
        return self.text == eps or self.ref == eps

    def has_initial_capital(self):
        if len(self.ref) >= 1 and self.ref[0].isupper():
            return True
        work = clean_text(self.ref, self.PUNCT, False)
        if work == "":
            return False
        return work[0].isupper()
    
    def maybe_sentence_start(self, conjunctions):
        return self.has_initial_capital() or self.text in conjunctions

    def has_sentence_final(self):
        work_ref = self.ref
        FINALS = [".", "!", "?"]
        l = len(work_ref)
        j = -1
        if l >= 1 and work_ref[-1] in FINALS:
            return True
        while j >= -l and work_ref[j] in self.PUNCT:
            if work_ref[j] in FINALS:
                return True
            j -= 1
        return False

    def set_inserted_conjunction(self, edit="ins-conj"):
        self.edit = edit


def ctm_from_file(filename):
    ctm_lines = []
    with open(filename) as input:
        for line in input.readlines():
            ctm_lines.append(CTMEditLine(line.strip()))
    return ctm_lines


def merge_consecutive(ctm_a, ctm_b, text="", joiner="", epsilon="<eps>", edit=""):
    new_ctm = copy.deepcopy(ctm_a)
    new_ctm.end_time = ctm_b.end_time
    new_ctm.duration = new_ctm.end_time - new_ctm.start_time
    if text == "":
        new_ctm.text = joiner.join([ctm_a.text, ctm_b.text]).replace(epsilon, "")
        new_ctm.ref = joiner.join([ctm_a.ref, ctm_b.ref]).replace(epsilon, "")
        if edit == "":
            new_ctm.edit = "cor"
        else:
            new_ctm.edit = edit
    else:
        new_ctm.text = text
        new_ctm.ref = text
        new_ctm.edit = "cor"
    return new_ctm


def shift_epsilons(ctmedits: List[CTMEditLine], comparison=_approx_match, backward=False, ref=True, epsilon="<eps>"):
    def is_eps(ctmedit):
        if ref:
            return ctmedit.ref == epsilon
        else:
            return ctmedit.text == epsilon
    def set_eps(ctmedit):
        if ref:
            ctmedit.ref = epsilon
            ctmedit.edit = "ins"
        else:
            ctmedit.text = epsilon
            ctmedit.edit = "del"

    if backward:
        ctmedits.reverse()

    if comparison is None:
        comparison = lambda x, y: x == y

    i = j = 0
    while i < len(ctmedits):
        first_line = ctmedits[i]
        if not is_eps(first_line):
            i += 1
            continue
        else:
            j = i + 1
            while j < len(ctmedits):
                second_line = ctmedits[j]
                text = first_line.text if ref else second_line.text
                if is_eps(second_line):
                    j += 1
                    continue
                else:
                    other = second_line.ref if ref else first_line.ref
                    if comparison(text, other):
                        if ref:
                            first_line.text = first_line.ref = second_line.ref
                            first_line.edit = "cor"
                            set_eps(second_line)
                        else:
                            first_line.text = first_line.ref
                            first_line.edit = "cor"
                            set_eps(second_line)
                    break
        i += 1

    if backward:
        ctmedits.reverse()

    return ctmedits


def check_and_swap_ending(first: CTMEditLine, second: CTMEditLine, conjunctions: List[str] = [], epsilon="<eps>"):
    if first.edit != "ins" and second.edit != "sub":
        return
    if not _approx_match(first.text, second.ref):
        return
    if not first.ref == epsilon:
        return
    if not second.text in conjunctions:
        return
    first.text = second.ref
    first.edit = "cor"
    second.ref = epsilon
    second.set_inserted_conjunction()


def all_correct(ctmedits: List[CTMEditLine], acceptable: List[str] = None):
    def is_acceptable(a):
        return acceptable is not None and a in acceptable
    def is_correct(a):
        return a == "cor" or is_acceptable(a)
    for line in ctmedits:
        if not is_correct(line.edit):
            return False
    return True


def split_sentences(ctmedits: List[CTMEditLine], conjunctions: List[str] = []):
    sentences = []
    current = []
    i = 0
    while i < len(ctmedits):
        window = ctmedits[i:i+2]
        if len(window) == 2:
            if window[0].has_sentence_final() and window[1].maybe_sentence_start(conjunctions):
                current.append(window[0])
                sentences.append(current)
                current = []
            else:
                current.append(window[0])
        else:
            current.append(window[0])
            sentences.append(current)
            current = []
        i += 1
    if current != []:
        sentences.append(current)
    return sentences


def generate_filename(ctmlines: List[CTMEditLine]):
    file_id = ctmlines[0].id
    start = ctmlines[0].start_time
    end = ctmlines[-1].end_time
    seg_dur = end - start
    filename = f"{file_id}_{start}_{seg_dur}.ctmedit"
    return filename