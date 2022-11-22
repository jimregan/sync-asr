from .elements import TimedWord, TimedElement


class CTMLine(TimedWord):
    def __init__(self, *args, **kwargs):
        super(TimedElement, self).__init__(*args, **kwargs)
        if len(args) >= 1:
            self.from_line(args[0])
        elif "from_line" in kwargs:
            self.from_line(kwargs["from_line"])

    def __str__(self) -> str:
        return " ".join(self.as_list())

    def __repr__(self) -> str:
        return f"{self.id} ({self.start_time, self.end_time}) {self.text}"

    def from_line(self, text: str):
        # AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0
        parts = text.strip().split()
        self.id = parts[0]
        self.channel = parts[1]
        self.start_time = int(float(parts[2]) * 1000)
        self.duration = int(float(parts[3]) * 1000)
        self.end_time = self.start_time + self.duration
        self.text = parts[4]
        self.confidence = float(parts[5])

    def as_list(self):
        return [
            self.id,
            self.channel,
            str(float(self.start_time / 1000)),
            str(float(self.duration / 1000)),
            self.text,
            str(self.confidence),
        ]


def ctm_from_file(filename):
    ctm_lines = []
    with open(filename) as input:
        for line in input.readlines():
            ctm_lines.append(CTMLine(from_line=line.strip()))
    return ctm_lines