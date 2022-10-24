from .elements import TimedElement
import collections
from itertools import islice

try:
    import webvtt
except ImportError:
    class VTTInput(TimedElement):
        pass


    class VTTCaption(TimedElement):
        pass


_SENT_ENDS = [".", "?", "!"]


# https://docs.python.org/3/library/itertools.html#recipes
def sliding_window(iterable, n):
    # sliding_window('ABCDEFG', 4) -> ABCD BCDE CDEF DEFG
    it = iter(iterable)
    window = collections.deque(islice(it, n), maxlen=n)
    if len(window) == n:
        yield tuple(window)
    for x in it:
        window.append(x)
        yield tuple(window)


class VTTInput(TimedElement):
    def __init__(self, filename):
        self.splittable = False
        self.merge_next = False
        self._load(filename)

    def _load(self, filename):
        captions = webvtt.read(filename)
        self.captions = []
        for caption in captions:
            self.captions.append(VTTCaption(caption))

    def merge_captions(self):
        def merge_actual(l):
            start = l[0].start
            end = l[-1].end
            text = " ".join([t.text for t in l])
            return VTTCaption(start, end, text)
        i = 0
        tmp = []
        buf = []
        while i < len(self.captions):
            if self.captions[i].text[-1] in _SENT_ENDS:
                buf.append(self.captions[i])
                if len(buf) == 1:
                    yield buf[0]
                else:
                    yield merge_actual(buf)
                buf = []
            else:
                buf.append(self.captions[i])





class VTTCaption(TimedElement):
    def __init__(self, caption=None, **kwargs):
        reqd = ["start_time", "end_time", "text"]
        if caption is not None:
            start = int(caption.start_in_seconds * 1000)
            end = int(caption.end_in_seconds * 1000)
            text = caption.text
        else:
            for req in reqd:
                if not req in kwargs:
                    raise ValueError(f"Missing required argument {req}")
            super(TimedElement, self).__init__(kwargs["start_time"], kwargs["end_time"], kwargs["text"])

        super(TimedElement, self).__init__(start_time=start, end_time=end, text=text)
        self.start_original = caption.start
        self.end_original = caption.end