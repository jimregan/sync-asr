from typing import List


class TimedElement():
    def __init__(self, start_time="", end_time="", text=""):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

    def __str__(self) -> str:
        return f"[{self.start_time},{self.end_time}] {self.text}"

    def _is_valid_comparison(self, other):
        return (hasattr(other, "start_time") and
                hasattr(other, "end_time") and
                hasattr(other, "text"))

    def get_duration(self):
        if "duration" in self.__dict__:
            return self.duration
        else:
            return self.end_time - self.start_time

    def within(self, other):
        if not self._is_valid_comparison(other):
            return NotImplemented
        return (self.end_time <= other.end_time and
                self.start_time >= other.start_time)

    def __gt__(self, other):
        """Strictly greater than: self completely contains other"""
        return (self.start_time < other.start_time and self.end_time > other.end_time)

    def __lt__(self, other):
        """Strictly less than: other completely contains self"""
        return (self.start_time > other.start_time and self.end_time < other.end_time)

    def has_overlap(self, other):
        if not hasattr(other, "duration"):
            return NotImplemented
        if not self._is_valid_comparison(other):
            return NotImplemented
        if self.end_time < other.end_time:
            return self.end_time > other.start_time
        elif self.start_time > other.start_time:
            return self.start_time < other.end_time

    def contained_duration(self, other):
        if not hasattr(other, "duration"):
            return NotImplemented

    def overlap(self, other):
        if not self._is_valid_comparison(other):
            return NotImplemented
        if self.start_time < other.start_time:
            min1, min2 = self.start_time, other.start_time
        else:
            min2, min1 = self.start_time, other.start_time
        if self.end_time > other.end_time:
            max1, max2 = self.end_time, other.end_time
        else:
            max2, max1 = self.end_time, other.end_time
        return max(0, min(max1, max2) - max(min1, min2))

    def pct_overlap(self, other):
        """Percentage of how much of this is contained by other"""
        if not hasattr(other, "duration"):
            return NotImplemented
        if not self.has_overlap(other):
            return 0.0
        if self.within(other):
            return 100.0
        return (self.overlap(other) / self.get_duration()) * 100

    def has_enough_overlap(self, other, cutoff=90):
        return self.pct_overlap(other) >= cutoff


class TimedSentence(TimedElement):
    def __init__(self, *args, **kwargs):
        super(TimedElement, self).__init__(*args, **kwargs)

    def get_words(self):
        return self.text.split(" ")


class TimedWord(TimedElement):
    def __init__(self, *args, **kwargs):
        super(TimedElement, self).__init__(*args, **kwargs)


class TimedWordSentence(TimedElement):
    def __init__(self, words: List[TimedWord]):
        start_time = words[0].start_time
        end_time = words[-1].end_time
        text = " ".join([w.text for w in words])
        super.__init__(start_time, end_time, text)
        self.words = words

    def words_indexed(self):
        return zip(self.words, range(0, len(self.words)))
