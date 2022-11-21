from .elements import TimedWord, TimedElement


class CTMEditLine(TimedWord):
    def __init__(self, *args, **kwargs):
        super(TimedElement, self).__init__(*args, **kwargs)

    def __str__(self) -> str:
        return " ".join(self.as_list())

    def from_line(self, text: str):
        # AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil tainted
        parts = text.strip().split()
        EDITS = ["cor", "ins", "del", "sub"]
        self.id = parts[0]
        self.channel = parts[1]
        self.start_time = float(parts[2]) * 1000
        self.duration = float(parts[3]) * 1000
        self.end_time = self.start_time + self.duration
        self.text = parts[4]
        self.confidence = float(parts[5])
        self.ref = parts[6]
        if parts[7] in EDITS:
            self.edit = parts[7]
        else:
            raise ValueError(f"Unknown edit type: {parts[7]}")
        if len(parts) == 9:
            if parts[8] == "tainted":
                self.tainted = True

    def as_list(self):
        out = [
            self.id,
            self.channel,
            float(self.start_time / 1000),
            float(self.duration / 1000),
            self.text,
            self.confidence,
            self.ref,
            self.edit, 
        ]
        if self.tainted:
            out.append("tainted")
        return out
    
    def mark_correct_from_list(self, collisions):
        def checksout(ref, col):
            return ((type(col) == str and ref == col) or \
                (type(col) == list and ref in col))
        if self.text in collisions:
            collision = collisions[self.text]
            if checksout(self.ref, collision):
                self.text = self.ref
                self.edit = "cor"

    def fix_case_difference(self):
        PUNCT = [".", ",", ":", ";", "!", "?", "-"]
        comp = self.ref
        if comp[-1] in PUNCT:
            comp = comp[:-1]
        if self.text == comp.lower():
            self.text = self.ref
            self.edit = "cor"
