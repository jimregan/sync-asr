# Copyright (c) 2026, Jim O'Regan for Språkbanken Tal
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
from sync_asr.alignment import (
    AlignedSequence,
    RepeatedTokenHeuristic,
    WordPairDictionaryHeuristic,
    align_text,
    bridge_gaps,
    is_text_gap,
)
from sync_asr.elements import TimedElement
from sync_asr.riksdag.time_aligner import AlignedGroup


def test_aligned_sequence_span_uses_timed_side_only():
    a = [TimedElement(0, 100, "a0"), "untimed_ref_word"]
    b = [TimedElement(0, 50, "b0"), TimedElement(50, 120, "b1")]
    groups = [AlignedGroup([0], [0, 1], "overlap", {"match_method": "time_overlap"})]
    seq = AlignedSequence(a, b, groups, method="test")
    assert seq.start_time == 0
    assert seq.end_time == 120


def test_aligned_sequence_no_timed_nodes_is_zero_width():
    seq = AlignedSequence(["x"], ["y"], [AlignedGroup([0], [0], "cor", {})], method="text")
    assert seq.start_time == 0
    assert seq.end_time == 0


def test_aligned_sequence_carries_own_annotations_independent_of_groups():
    seq = AlignedSequence([], [], [], method="test", annotations={"pass": "word_level"})
    assert seq.annotations == {"pass": "word_level"}


def test_aligned_sequence_comparable_via_inherited_timed_element_methods():
    a = [TimedElement(0, 100, "a0")]
    b = [TimedElement(0, 50, "b0"), TimedElement(50, 120, "b1")]
    word_pass = AlignedSequence(a, b, [AlignedGroup([0], [0, 1], "overlap", {})], method="word")
    phon_pass = AlignedSequence(a, b, [AlignedGroup([0], [0], "overlap", {})], method="phonetic")

    assert phon_pass.within(word_pass) is True
    assert word_pass.contains(phon_pass) is True
    assert word_pass.within(phon_pass) is False


def test_repeated_token_heuristic_matches_worked_example():
    # ref "A, B och C" -> ["a", "b", "och", "c"]; hyp "A och B och C" ->
    # ["a", "och", "b", "och", "c"] -- the worked example as given.
    heuristic = RepeatedTokenHeuristic(distributable_tokens={"och", "eller"})
    a_span = ["a", "b", "och", "c"]
    b_span = ["a", "och", "b", "och", "c"]

    groups = heuristic.match(a_span, b_span)

    assert groups is not None
    # every a-index and every b-index is accounted for exactly once
    seen_a = sorted(i for g in groups for i in g.a_indices)
    seen_b = sorted(j for g in groups for j in g.b_indices)
    assert seen_a == [0, 1, 2, 3]
    assert seen_b == [0, 1, 2, 3, 4]
    assert all(g.metadata["heuristic"] == "repeated_token_paraphrase" for g in groups)
    assert all(g.metadata["accepted"] is True for g in groups)
    # the extra, non-item-adjacent occurrence is flagged as an accepted
    # insertion, not silently dropped
    ins_groups = [g for g in groups if g.kind == "ins"]
    assert len(ins_groups) == 1
    assert ins_groups[0].a_indices == []
    assert ins_groups[0].b_indices == [1]


def test_repeated_token_heuristic_not_specific_to_conjunctions():
    # the same mechanism applied to a caller-named non-conjunction
    # particle, to demonstrate it's a general reduced/expanded-token
    # pattern rather than something baked in for "och"/"eller" specifically.
    heuristic = RepeatedTokenHeuristic(distributable_tokens={"the"})
    groups = heuristic.match(["the", "cat", "dog"], ["the", "cat", "the", "dog"])
    assert groups is not None
    seen_a = sorted(i for g in groups for i in g.a_indices)
    seen_b = sorted(j for g in groups for j in g.b_indices)
    assert seen_a == [0, 1, 2]
    assert seen_b == [0, 1, 2, 3]


def test_repeated_token_heuristic_rejects_non_matching_items():
    heuristic = RepeatedTokenHeuristic(distributable_tokens={"och"})
    assert heuristic.match(["a", "b", "och", "c"], ["a", "och", "b", "och", "d"]) is None


def test_repeated_token_heuristic_rejects_single_item():
    heuristic = RepeatedTokenHeuristic(distributable_tokens={"och"})
    assert heuristic.match(["a"], ["a"]) is None


def test_word_pair_dictionary_heuristic_interface_no_data_bundled():
    # deliberately fabricated equivalence, just to exercise the interface --
    # no real grammatical data is bundled in the library itself.
    equivalences = {("gjorde",): ("har", "gjort")}
    heuristic = WordPairDictionaryHeuristic("grammatical_alternation", equivalences)

    groups = heuristic.match(["gjorde"], ["har", "gjort"])
    assert groups == [AlignedGroup([0], [0, 1], "cor",
                                    {"heuristic": "grammatical_alternation", "accepted": True})]
    assert heuristic.match(["gjorde"], ["gör"]) is None


def test_bridge_gaps_is_additive_not_destructive():
    a = ["a", "b", "och", "c"]
    b = ["a", "och", "b", "och", "c"]
    gap_group = AlignedGroup([0, 1, 2, 3], [0, 1, 2, 3, 4], "sub", {})
    seq = AlignedSequence(a, b, [gap_group], method="text")

    heuristic = RepeatedTokenHeuristic(distributable_tokens={"och"})
    bridge_gaps(seq, [heuristic], is_gap=lambda g: g.kind == "sub")

    # the original, unresolved group is still present
    assert gap_group in seq.groups
    # plus the heuristic's bridge groups, rebased onto the parent sequence
    bridged = [g for g in seq.groups if g is not gap_group]
    assert len(bridged) == 5
    seen_a = sorted(i for g in bridged for i in g.a_indices)
    seen_b = sorted(j for g in bridged for j in g.b_indices)
    assert seen_a == [0, 1, 2, 3]
    assert seen_b == [0, 1, 2, 3, 4]


def test_bridge_gaps_ignores_non_gap_groups():
    a = ["a"]
    b = ["a"]
    resolved_group = AlignedGroup([0], [0], "cor", {"match_method": "direct"})
    seq = AlignedSequence(a, b, [resolved_group], method="text")

    heuristic = RepeatedTokenHeuristic(distributable_tokens={"och"})
    bridge_gaps(seq, [heuristic], is_gap=lambda g: g.kind == "sub")

    assert seq.groups == [resolved_group]


def test_align_text_anchors_and_leaves_gap_unresolved_without_heuristics():
    # difflib's own LCS matching already resolves simple repeated-token
    # insertions for free (verified separately: "a b och c" vs
    # "a och b och c" comes back as equal+insert+equal, no gap at all) --
    # so to exercise a genuine, unresolved gap here we need a span with no
    # shared subsequence at all, like a grammatical alternation.
    ref = ["x", "gjorde", "y"]
    hyp = ["x", "har", "gjort", "y"]

    seq = align_text(ref, hyp)

    cor_groups = [g for g in seq.groups if g.kind == "cor"]
    assert [(g.a_indices, g.b_indices) for g in cor_groups] == [([0], [0]), ([2], [3])]
    assert all(g.metadata["match_method"] == "text_equal" for g in cor_groups)

    gap_groups = [g for g in seq.groups if is_text_gap(g)]
    assert len(gap_groups) == 1
    assert gap_groups[0].kind == "sub"
    assert gap_groups[0].a_indices == [1]
    assert gap_groups[0].b_indices == [1, 2]


def test_align_text_applies_heuristics_in_advance():
    ref = ["x", "gjorde", "y"]
    hyp = ["x", "har", "gjort", "y"]
    heuristic = WordPairDictionaryHeuristic(
        "grammatical_alternation", {("gjorde",): ("har", "gjort")}
    )

    seq = align_text(ref, hyp, heuristics=[heuristic])

    # the raw, unresolved gap is still there (non-destructive)...
    gap_groups = [g for g in seq.groups if g.kind == "sub"]
    assert len(gap_groups) == 1
    # ...alongside the heuristic's accepted bridge group over the same span
    bridged = [g for g in seq.groups if g.metadata.get("heuristic") == "grammatical_alternation"]
    assert len(bridged) == 1
    assert bridged[0].a_indices == [1]
    assert bridged[0].b_indices == [1, 2]
    assert bridged[0].metadata["accepted"] is True


def test_align_text_heuristics_can_be_applied_later_instead():
    ref = ["x", "gjorde", "y"]
    hyp = ["x", "har", "gjort", "y"]
    heuristic = WordPairDictionaryHeuristic(
        "grammatical_alternation", {("gjorde",): ("har", "gjort")}
    )

    # built with no heuristics available yet...
    seq = align_text(ref, hyp)
    assert not any(g.metadata.get("heuristic") for g in seq.groups)

    # ...refined later, once the heuristic (or the context/dictionary it
    # needs) becomes available.
    bridge_gaps(seq, [heuristic], is_gap=is_text_gap)

    bridged = [g for g in seq.groups if g.metadata.get("heuristic") == "grammatical_alternation"]
    assert len(bridged) == 1
