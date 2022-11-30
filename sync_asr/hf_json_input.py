from .elements import TimedElement, TimedWord
from typing import List
import json


class HuggingFaceJSON(TimedElement):
    def __init__(self, data=None, filename=""):
        if data is None and filename != "":
            self._load(filename)
        elif filename == "":
            self._grab(data)
        #self.words: List[TimedWord] = []
        self.verbose = True
        self.words = []

    def _load(self, filename):
        with open(filename) as jsonf:
            data = json.load(jsonf)
            if not "chunks" in data:
                raise ValueError(f"File {filename} does not appear to contain HuggingFace JSON")
            self._grab(data, False)

    def _grab(self, data):
        if type(data) == str:
            data = json.loads(data)
        if self.verbose and (not "chunks" in data or type(data["chunks"]) != list):
            raise ValueError(f"Data does not appear to contain HuggingFace JSON")
        if self.verbose and len(data["chunks"]) == 0:
            raise ValueError(f"Data appears to lack content")
        for chunk in data["chunks"]:
            if self.verbose:
                print(f'Reading chunk: {chunk["timestamp"][0]}:{chunk["timestamp"][1]} {chunk["text"]}')
            self.words.append(TimedWord(start_time=int(chunk["timestamp"][0] * 1000),
                                        end_time=int(chunk["timestamp"][1] * 1000),
                                        text=chunk["text"]))
