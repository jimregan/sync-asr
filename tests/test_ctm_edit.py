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
from sync_asr.ctm_edit import CTMEditLine, shift_epsilons, split_sentences, all_correct
from sync_asr.riksdag.riksdag_align import rd_equals


_SAMPLE = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil tainted"
_SAMPLE2 = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil tainted spelling:both"
_SAMPLE3 = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil spelling:both"
_SAMPLE4 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 foo sub
"""
_EXP4 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 foo cor
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 <eps> ins
"""
_SAMPLE5 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 bar 1.0 foo sub
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 foo 1.0 <eps> ins
"""
_EXP5 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 foo 1.0 foo cor
"""
_SAMPLE6 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 foo del
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 <eps> 1.0 bar del
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 foo 1.0 bar sub
"""
_EXP6 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 foo cor
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 <eps> 1.0 bar del
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 <eps> 1.0 bar del
"""
_SAMPLE7 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 bar sub
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 <eps> 1.0 bar del
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 <eps> 1.0 foo del
"""
_EXP7 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 bar del
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 <eps> 1.0 bar del
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 foo 1.0 foo cor
"""
_SAMPLE8 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 Foo. sub
"""
_EXP8 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 Foo. 1.0 Foo. cor
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 <eps> ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 <eps> ins
"""
_SAMPLE9 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 Foo ins
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 bar. ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 Foo. sub
"""
_SAMPLE9A = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 Foo ins
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 bar. ins
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 bar 1.0 Foo. sub
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 Foo ins
"""
_SAMPLE10 = """
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 Foo cor
AJJacobs_2007P-0001605-0003029 1 0.1 0.09 bar 1.0 bar. cor
AJJacobs_2007P-0001605-0003029 1 0.2 0.09 foo 1.0 Foo. cor
AJJacobs_2007P-0001605-0003029 1 0 0.09 foo 1.0 Foo cor
"""

PARAPHRASE_EXAMPLE = """
2442207020017513221 1 2032.34 0.08 Det 1.0 Det cor
2442207020017513221 1 2032.46 0.339 handlar 1.0 handlar cor
2442207020017513221 1 2032.94 0.079 som 1.0 <eps> ins
2442207020017513221 1 2033.06 0.059 vi 1.0 <eps> ins
2442207020017513221 1 2033.18 0.419 debatterade 1.0 <eps> ins
2442207020017513221 1 2033.68 0.2 förra 1.0 <eps> ins
2442207020017513221 1 2033.96 0.399 veckan 1.0 <eps> ins
2442207020017513221 1 2035.0 0.119 om 1.0 om cor
2442207020017513221 1 2035.38 1.119 brottsoffrets 1.0 brottsoffrets cor
2442207020017513221 1 2036.6 0.12 och 1.0 och cor
2442207020017513221 1 2036.84 0.48 samhällets 1.0 samhällets cor
2442207020017513221 1 2037.32 0.0 <eps> 1.0 upprättelse, del
2442207020017513221 1 2037.32 0.0 <eps> 1.0 som del
2442207020017513221 1 2037.32 0.0 <eps> 1.0 vi del
2442207020017513221 1 2037.32 0.0 <eps> 1.0 debatterade del
2442207020017513221 1 2037.32 0.0 <eps> 1.0 förra del
2442207020017513221 1 2037.38 0.659 upprättelse 1.0 veckan. sub
"""


def test_ctmline():
    ctm_line = CTMEditLine(_SAMPLE)
    assert ctm_line.id == "AJJacobs_2007P-0001605-0003029"
    assert ctm_line.channel == "1"
    assert ctm_line.start_time == 0
    assert ctm_line.duration == 90
    assert ctm_line.text == "<eps>"
    assert ctm_line.confidence == 1.0
    assert ctm_line.ref == "<eps>"
    assert ctm_line.edit == "sil"
    assert ctm_line.tainted == True


def test_ctmline2():
    ctm_line = CTMEditLine(_SAMPLE2)
    assert ctm_line.tainted == True
    assert "spelling" in ctm_line.props
    assert ctm_line.props["spelling"] == "both"


def test_ctmline3():
    ctm_line = CTMEditLine(_SAMPLE3)
    assert "tainted" not in ctm_line.__dict__
    assert "spelling" in ctm_line.props
    assert ctm_line.props["spelling"] == "both"


def test_as_list():
    ctm_line = CTMEditLine(_SAMPLE)
    exp = ["AJJacobs_2007P-0001605-0003029", "1", "0.0", "0.09", "<eps>", "1.0", "<eps>", "sil", "tainted"]
    assert ctm_line.as_list() == exp


def test_shift_epsilons():
    ctmlines4 = [CTMEditLine(x) for x in _SAMPLE4.split("\n") if x != ""]
    explines4 = [CTMEditLine(x) for x in _EXP4.split("\n") if x != ""]
    ctmout = shift_epsilons(ctmlines4, comparison=None, backward=False, ref=True)
    assert explines4 == ctmout
    ctmlines5 = [CTMEditLine(x) for x in _SAMPLE5.split("\n") if x != ""]
    explines5 = [CTMEditLine(x) for x in _EXP5.split("\n") if x != ""]
    ctmout = shift_epsilons(ctmlines5, comparison=None, backward=True, ref=True)
    assert explines5 == ctmout
    ctmlines6 = [CTMEditLine(x) for x in _SAMPLE6.split("\n") if x != ""]
    explines6 = [CTMEditLine(x) for x in _EXP6.split("\n") if x != ""]
    ctmout = shift_epsilons(ctmlines6, comparison=None, backward=False, ref=False)
    assert explines6 == ctmout
    ctmlines7 = [CTMEditLine(x) for x in _SAMPLE7.split("\n") if x != ""]
    explines7 = [CTMEditLine(x) for x in _EXP7.split("\n") if x != ""]
    ctmout = shift_epsilons(ctmlines7, comparison=None, backward=True, ref=False)
    assert explines7 == ctmout
    ctmlines8 = [CTMEditLine(x) for x in _SAMPLE8.split("\n") if x != ""]
    explines8 = [CTMEditLine(x) for x in _EXP8.split("\n") if x != ""]
    ctmout = shift_epsilons(ctmlines8, comparison=rd_equals, backward=False, ref=True)
    assert explines8 == ctmout


def test_split_sentences():
    lines = [CTMEditLine(x) for x in _SAMPLE9.split("\n") if x != ""]
    sentences = split_sentences(lines)
    assert len(sentences) == 2
    lines = [CTMEditLine(x) for x in _SAMPLE9A.split("\n") if x != ""]
    sentences = split_sentences(lines)
    assert len(sentences) == 3


def test_split_sentences():
    lines = [CTMEditLine(x) for x in _SAMPLE9.split("\n") if x != ""]
    assert all_correct(lines) == False
    lines = [CTMEditLine(x) for x in _SAMPLE10.split("\n") if x != ""]
    assert all_correct(lines) == True
