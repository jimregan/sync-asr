from sync_asr.elements import TimedElement


def test_timed_element():
    te = TimedElement(0, 200, "test")
    assert te.start_time == 0
    assert te.end_time == 200
    assert te.text == "test"
    assert te.get_duration() == 200
    te2 = TimedElement(10, 180, "es")
    assert (te > te2) == True


def test_has_overlap():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.has_overlap(te2) == True