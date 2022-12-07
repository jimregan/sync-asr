from sync_asr.ctm_edit import CTMEditLine, shift_epsilons


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
    ctmout = shift_epsilons(ctmout, comparison=None, forward=False, ref=True)
    assert explines4 == ctmout