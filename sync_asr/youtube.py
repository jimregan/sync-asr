try:
    import youtube_dl
except ImportError:
    print("Could not import youtube-dl")
    print("Hint: pip install youtube-dl")
    if __name__ == '__main__':
        quit()


    class YoutubeWrapper():
        pass


_OUTTMPL = '%(id)s.%(ext)s'
_YDL_OPTS = {
    "writesubtitles": True,
    "subtitlesformat": "vtt",
    "writeinfojson": True,
    "outtmpl": _OUTTMPL,
}


_LIC="Creative Commons Attribution license (reuse allowed)"


class YoutubeWrapper:
    """
    Wrapper around youtube-dl
    This class offers nothing real, but specifies a
    number of defaults
    """
    def __init__(self) -> None:
        self.ydl = youtube_dl.YoutubeDL(_YDL_OPTS)
        self.urls = []

    def add_url(self, url: str):
        self.urls.append(url)

    def run(self):
        self.ydl.download(self.urls)