# Copyright (c) 2022, Jim O'Regan for Språkbanken Tal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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