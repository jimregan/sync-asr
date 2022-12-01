from sync_asr.ctm_taint_spelling import HunspellChecker
from pathlib import Path

can_run = True
try:
    import hunspell
except ImportError:
    can_run = False


SWE_DICT = "/usr/share/hunspell/sv_SE.dic"
SWE_AFF = "/usr/share/hunspell/sv_SE.aff"


def test_hunspell_checker():
    can_run = (Path(SWE_DICT).exists() and Path(SWE_AFF).exists())
    if can_run:
        speller = HunspellChecker(SWE_DICT, SWE_AFF)
        assert speller.check("blåbär") == True
        assert speller.check_pair("blåbär", "blåbär") == "correct_both"
        assert speller.check_pair("blåbär", "blabär") == "correct_text"
        assert speller.check_pair("blåbar", "blåbär") == "correct_ref"
        assert speller.check_pair("blåbar", "blabär") == "incorrect_both"