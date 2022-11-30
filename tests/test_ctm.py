from sync_asr.ctm import CTMLine


_SAMPLE = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0"


def test_ctmline():
    ctm_line = CTMLine(_SAMPLE)
    assert ctm_line.id == "AJJacobs_2007P-0001605-0003029"
    assert ctm_line.channel == "1"
    assert ctm_line.start_time == 0
    assert ctm_line.duration == 900
    assert ctm_line.text == "<eps>"
    assert ctm_line.confidence == 1.0