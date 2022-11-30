from sync_asr.ctm import CTMLine


_SAMPLE = "AJJacobs_2007P-0001605-0003029 1 0 0.09 <eps> 1.0"


def test_ctmline():
    ctm_line = CTMLine(_SAMPLE)