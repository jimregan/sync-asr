from .elements import TimedWordSentence, TimedWord
import json


class HuggingFaceJSON(TimedWordSentence):
    def __init__(self, data=None, filename=""):
        if data is None:
            words = self._load(filename)
        elif filename == "":
            words = self._grab(data)
        super().__init__(words)

    def _load(self, filename):
        with open(filename) as jsonf:
            data = json.load(jsonf)
            if not "chunks" in data:
                raise ValueError(f"File {filename} does not appear to contain HuggingFace JSON")
            return self._grab(data, False)

    def _grab(self, data, warn=False):
        words = []
        if type(data) == str:
            data = json.loads(data)
        if not "chunks" in data or type(data["chunks"]) != list:
            raise ValueError(f"Data does not appear to contain HuggingFace JSON")
        for chunk in data["chunks"]:
            if warn:
                print(f'Reading chunk: {chunk["timestamp"][0]}:{chunk["timestamp"][1]} {chunk["text"]}')
            words.append(TimedWord(start_time=int(chunk["timestamp"][0] * 1000),
                                        end_time=int(chunk["timestamp"][1] * 1000),
                                        text=chunk["text"]))
        return words
