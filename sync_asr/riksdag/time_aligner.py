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


def end_cost(a, b):
    return abs(a["end"] - b["end"])


def start_cost(a, b):
    return abs(a["start"] - b["start"])


def cost(a, b):
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

