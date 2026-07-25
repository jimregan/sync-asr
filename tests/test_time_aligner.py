# Copyright (c) 2024, Jim O'Regan for Språkbanken Tal
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
from sync_asr.elements import TimedElement
from sync_asr.riksdag.time_aligner import align


def E(start, end, text=""):
    return TimedElement(start, end, text)


def test_all_exact():
    a = [E(0, 50, "a0"), E(50, 100, "a1"), E(100, 150, "a2")]
    b = [E(0, 50, "b0"), E(50, 100, "b1"), E(100, 150, "b2")]
    groups = align(a, b)
    assert [g.kind for g in groups] == ["exact", "exact", "exact"]
    assert [g.a_indices for g in groups] == [[0], [1], [2]]
    assert [g.b_indices for g in groups] == [[0], [1], [2]]


def test_one_to_many():
    a = [E(0, 100, "word")]
    b = [E(0, 40, "p0"), E(40, 70, "p1"), E(70, 100, "p2")]
    groups = align(a, b)
    assert len(groups) == 1
    assert groups[0].kind == "overlap"
    assert groups[0].a_indices == [0]
    assert groups[0].b_indices == [0, 1, 2]


def test_many_to_one():
    a = [E(0, 50, "w0"), E(50, 100, "w1")]
    b = [E(0, 100, "p0")]
    groups = align(a, b)
    assert len(groups) == 1
    assert groups[0].kind == "overlap"
    assert groups[0].a_indices == [0, 1]
    assert groups[0].b_indices == [0]


def test_prefers_one_to_one_within_ambiguous_component():
    # a0 overlaps b0 heavily and b1 slightly; a1 overlaps b1 heavily and b0
    # slightly -- greedy max-overlap should still recover the natural 1:1
    # pairing (a0,b0) and (a1,b1) inside a single connected component.
    a = [E(0, 55, "w0"), E(50, 100, "w1")]
    b = [E(0, 50, "p0"), E(45, 100, "p1")]
    groups = align(a, b)
    assert [g.kind for g in groups] == ["overlap", "overlap"]
    assert groups[0].a_indices == [0]
    assert groups[0].b_indices == [0]
    assert groups[1].a_indices == [1]
    assert groups[1].b_indices == [1]


def test_unmatched_trailing_b():
    a = [E(0, 50, "w0")]
    b = [E(0, 50, "p0"), E(100, 120, "junk")]
    groups = align(a, b)
    assert [g.kind for g in groups] == ["exact", "unmatched_b"]
    assert groups[1].a_indices == []
    assert groups[1].b_indices == [1]


def test_unmatched_leading_a():
    a = [E(0, 20, "silence"), E(50, 100, "w0")]
    b = [E(50, 100, "p0")]
    groups = align(a, b)
    assert [g.kind for g in groups] == ["unmatched_a", "exact"]
    assert groups[0].a_indices == [0]
    assert groups[0].b_indices == []


def test_ordering_across_multiple_gaps():
    a = [E(0, 100, "w0"), E(100, 150, "w1"), E(150, 200, "w2")]
    b = [E(0, 40, "p0"), E(40, 100, "p1"), E(100, 150, "p2"), E(150, 200, "p3")]
    groups = align(a, b)
    seen_a = [i for g in groups for i in g.a_indices]
    seen_b = [i for g in groups for i in g.b_indices]
    assert seen_a == sorted(seen_a) == [0, 1, 2]
    assert seen_b == sorted(seen_b) == [0, 1, 2, 3]
