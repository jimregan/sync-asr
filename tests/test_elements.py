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
from sync_asr.elements import TimedElement, TimedSentence, TimedWord, TimedWordSentence


def test_timed_element():
    te = TimedElement(0, 200, "test")
    assert te.start_time == 0
    assert te.end_time == 200
    assert te.text == "test"
    assert te.get_duration() == 200
    te2 = TimedElement(10, 180, "es")
    assert (te > te2) == True
    assert f"{te}" == "[0,200] test"


def test_timed_element_annotations_default_empty_and_independent():
    te = TimedElement(0, 200, "test")
    assert te.annotations == {}
    te2 = TimedElement(10, 180, "es")
    te.annotations["match_method"] = "exact_timing"
    assert te2.annotations == {}  # not a shared mutable default


def test_timed_element_annotations_constructor():
    te = TimedElement(0, 200, "test", annotations={"match_method": "time_overlap"})
    assert te.annotations == {"match_method": "time_overlap"}


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


def test_contains():
    te2 = TimedElement(10, 110, "test")
    te3 = TimedElement(0, 120, "test")
    assert te3.contains(te2) == True
    assert te2.contains(te3) == False


def test_within_tolerance():
    # a word spilling 2 units past a conservative-bound window's end
    word = TimedElement(5, 22, "word")
    window = TimedElement(0, 20, "window")
    assert word.within(window) is False
    assert word.within(window, tolerance=1) is False
    assert word.within(window, tolerance=2) is True


def test_contains_tolerance():
    word = TimedElement(5, 22, "word")
    window = TimedElement(0, 20, "window")
    assert window.contains(word) is False
    assert window.contains(word, tolerance=2) is True


def test_has_overlap_tolerance():
    te1 = TimedElement(0, 10, "a")
    te2 = TimedElement(13, 20, "b")  # a 3-unit gap, no true overlap
    assert te1.has_overlap(te2) is False
    assert te1.has_overlap(te2, tolerance=2) is False
    assert te1.has_overlap(te2, tolerance=4) is True


def test_overlap_tolerance_bridges_a_gap():
    te1 = TimedElement(0, 10, "a")
    te2 = TimedElement(13, 20, "b")
    assert te1.overlap(te2) == 0
    assert te1.overlap(te2, tolerance=3) > 0


def test_default_tolerance_is_zero_and_backward_compatible():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.has_overlap(te2) == te1.has_overlap(te2, tolerance=0)
    assert te1.within(te2) == te1.within(te2, tolerance=0)


def test_overlap():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.overlap(te2) == 90


def test_pct_overlap():
    te1 = TimedElement(0, 100, "test")
    te2 = TimedElement(10, 110, "test")
    assert te1.pct_overlap(te2) == 90.0


def test_timed_sentence():
    ts = TimedSentence(0, 10, "this is a test")
    assert ts.start_time == 0
    assert ts.end_time == 10
    assert ts.get_words() == ["this", "is", "a", "test"]


def test_timed_word():
    tw = TimedWord(0, 200, "test")
    assert tw.start_time == 0
    assert tw.end_time == 200
    assert tw.text == "test"
    assert tw.get_duration() == 200
    tw2 = TimedWord(10, 180, "es")
    assert (tw > tw2) == True


def test_timed_word_sentence():
    tw1 = TimedWord(0, 200, "test")
    tw2 = TimedWord(200, 400, "test2")
    timed_words = [tw1, tw2]
    assert type(timed_words) == list
    tws = TimedWordSentence(timed_words)
    assert tws.start_time == 0
    assert tws.end_time == 400
    assert tws.text == "test test2"
    wi = [(tw1, 0), (tw2, 1)]
    assert tws.words_indexed() == wi