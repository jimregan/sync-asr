from .elements import TimedElement

try:
    import webvtt
except ImportError:
    class VTTInput(TimedElement):
        pass


    class VTTCaption(TimedElement):
        pass


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


class VTTCaption(TimedElement):
    def __init__(self, caption):
        start = int(caption.start_in_seconds * 1000)
        end = int(caption.end_in_seconds * 1000)
        text = caption.text
        super(TimedElement, self).__init__(start_time=start, end_time=end, text=text)
        self.start_original = caption.start
        self.end_original = caption.end