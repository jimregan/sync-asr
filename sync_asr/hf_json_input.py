from .elements import TimedElement, TimedWord
from typing import List
import json

class HuggingFaceJSON(TimedElement):
    words: List[TimedWord]

    def __init__(self, data=None, filename=""):
        self.foo = "foo"
        if data is None and filename != "":
            self._load(filename)

    def _load(self, filename):
        with open(filename) as jsonf:
            data = json.load(jsonf)
            if not "chunks" in data:
                raise ValueError(f"File {filename} does not appear to contain HuggingFace JSON")
            self._grab(data, False)

    def _grab(self, data, warn=True):
        if warn and not "chunks" in data:
            raise ValueError(f"Data does not appear to contain HuggingFace JSON")
        for chunk in data["chunks"]:
            self.words.append(TimedWord(start_time=chunk["timestamp"][0],
                                        end_time=chunk["timestamp"][1]),
                                        text=chunk["text"])
