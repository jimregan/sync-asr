import json
from pathlib import Path
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


def check_licence(filename):
    LIC="Creative Commons Attribution license (reuse allowed)"
    with open(filename) as jsonf:
        data = json.load(jsonf)
        if data["license"] == LIC:
            return True
    return False


def check_info_json_and_delete(dirname, keep_info=True):
    dirpath = Path(dirname)
    for info_json in dirpath.glob("*.info.json"):
        if not check_licence(str(info_json)):
            stem = info_json.stem.replace(".info", "")
            for skipped in dirpath.glob(f"{stem}.*"):
                if keep_info and str(skipped).endswith(".info.json"):
                    continue
                else:
                    skipped.unlink()

