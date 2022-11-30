from sync_asr.ctm_edit import CTMEditLine


_SAMPLE = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0 <eps> sil tainted"


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


def test_as_list():
    ctm_line = CTMEditLine(_SAMPLE)
    exp = ["AJJacobs_2007P-0001605-0003029", "1", "0.0", "0.09", "<eps>", "1.0", "<eps>", "sil", "tainted"]
    assert ctm_line.as_list() == exp