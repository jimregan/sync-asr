from .elements import TimedWord
import copy


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
        self.PUNCT = [".", ",", ":", ";", "!", "?", "-"]

    def __str__(self) -> str:
        return " ".join(self.as_list())

    def __repr__(self) -> str:
        return f"{self.id} ({self.start_time, self.end_time}) {self.text}|{self.ref}"

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
    
    def mark_correct_from_list(self, collisions, case_punct=False):
        def checksout(ref, col):
            return ((type(col) == str and ref == col) or \
                (type(col) == list and ref in col))
        work_ref = self.ref
        if case_punct:
            work_ref = self.ref.lower()
            if self.ref[-1] in self.PUNCT:
                work_ref = work_ref[:-1]
        if self.text in collisions:
            orig_text = self.text
            collision = collisions[self.text]
            if checksout(work_ref, collision):
                self.text = self.ref
                self.edit = "cor"
                if self.verbose:
                    self.set_prop("collision", f"{orig_text}_{work_ref}")

    def set_correct_ref(self):
        self.text = self.ref
        self.edit = "cor"

    def set_correct_text(self):
        self.ref = self.text
        self.edit = "cor"

    def fix_case_difference(self):
        comp = self.ref
        if comp[-1] in self.PUNCT:
            comp = comp[:-1]
        if self.text == comp.lower():
            self.set_correct_ref()

    def set_prop(self, key, value):
        self.props[key] = value

    def get_prop(self, key):
        return self.props[key]

    def has_eps(self, eps='"<eps>"'):
        return self.text == eps or self.ref == eps


def ctm_from_file(filename):
    ctm_lines = []
    with open(filename) as input:
        for line in input.readlines():
            ctm_lines.append(CTMEditLine(line.strip()))
    return ctm_lines


def merge_consecutive(ctm_a, ctm_b, text="", joiner="", epsilon='"<eps>"', edit=""):
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