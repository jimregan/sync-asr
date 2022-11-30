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


def test_within():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.within(te2) == False
    te3 = TimedElement(00, 120, "test")
    assert te2.within(te3) == True


def test_overlap():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.overlap(te2) == 90

def test_pct_overlap():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.pct_overlap(te2) == 90.0