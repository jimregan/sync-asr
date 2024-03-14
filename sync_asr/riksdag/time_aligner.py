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
import numpy as np


def end_cost(a, b):
    return abs(a["end"] - b["end"])


def start_cost(a, b):
    return abs(a["start"] - b["start"])


def total_cost(a, b):
    starts = start_cost(a, b)
    ends = end_cost(a, b)
    return starts + ends


def in_start_range(a, b, range=0.2):
    return abs(a["start"] - b["start"]) <= range


def in_end_range(a, b, range=0.2):
    return abs(a["end"] - b["end"]) <= range


def in_range(a, b, range=0.2):
    r_start = in_start_range(a, b, range)
    r_end = in_end_range(a, b, range)
    return r_start or r_end


def falls_between(a1, a2, b):
    if b["end"] <= a2["start"] and b["start"] >= a1["end"]:
        return True
    return False


def approx_eq(start1, start2, factor=0.04):
    return start1 == start2 or abs(start1 - start2) < factor


def align_times(new_a, new_b, merge_end_flexibility=0.06):
    s1 = len(new_a)
    s2 = len(new_b)

    additionals = []
    merges = {}

    dist_matrix = np.matrix(np.ones((s1, s2)))
    pair_cost = 0.0

    for i in range(s1):
        for j in range(s2):
            if not in_range(new_a[i], new_b[j]):
                continue

            if i == 0 and new_b[j]["end"] < new_a[0]["start"]:
                additionals.append((-1, 0, j))
                dist_matrix[i, j] = 1.0
                continue
            elif i < (s1 - 1) and falls_between(new_a[i], new_a[i + 1], new_b[j]):
                additionals.append((i, i + 1, j))
                dist_matrix[i, j] = 1.0
                continue
            elif i == s1 and new_b[j]["start"] >= new_a[i]["end"]:
                additionals.append((i, -1, j))
                dist_matrix[i, j] = 1.0
                continue

            if approx_eq(new_a[i]["start"], new_b[j]["start"]):
                tmp_j = j
                fwd = []
                extent = new_b[tmp_j]
                if i < (s1 - 2) and new_b[tmp_j]["end"] < new_a[i + 1]["end"]:
                    extent = new_a[i + 1]
                while tmp_j < (s2 - 1) and not in_end_range(new_a[i], extent, merge_end_flexibility):
                    fwd.append((end_cost(new_a[i], new_b[tmp_j]), tmp_j))
                    tmp_j += 1
                if len(fwd) > 1:
                    sfwd = sorted(fwd)
                    new_j = sfwd[0][1]
                    if new_j != j:
                        pair_cost = sfwd[0][0]
                        merges[i] = [x for x in range(j, new_j + 1)]
                        j = new_j
            if pair_cost != 1.:
                pair_cost = total_cost(new_a[i], new_b[j])
            dist_matrix[i, j] = pair_cost
    return dist_matrix, additionals, merges


def walk_matrix(dist_matrix, additions, merges):
    i = 0
    j = 0

    s1 = dist_matrix.shape[0]
    s2 = dist_matrix.shape[1]

    path = []
    def do_additions(i, j):
        if (i-1, i, j) in additions:
            return True
        if i+1 < s1 and (i, i + 1, j) in additions:
            return True
        if i == s1 and (i, -1, j) in additions:
            return True
        return False

    while i < s1:
        while j < s2:
            if not i in merges:
                if do_additions(i, j):
                    j += 1
                    continue
                pairs = []
                tmpj = j
                while tmpj < s2 - 1 and dist_matrix[i,tmpj] != 1.0:
                    pairs.append((dist_matrix[i,tmpj], tmpj))
                    tmpj += 1
                if pairs != []:
                    spairs = sorted(pairs)
                    j = spairs[0][1]
                path.append((i, j))
                i += 1
                j += 1
                continue
            else:
                path += [(i, x) for x in merges[i]]
                j = merges[i][-1] + 1
                i += 1
                continue
    return path

