# Copyright (c) 2023, Jim O'Regan for Språkbanken Tal
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
from sync_asr.riksdag.get_speaker_table import YearRange, merge_year_ranges


_TEST1_RAW = [
    ("2020-01-01", "2022-01-01"),
    ("2021-01-01", "2022-01-01"),
    ("2022-01-01", "2026-01-01"),
    ("2018-01-01", "2021-01-01"),
    ("2018-01-01", "2022-01-01"),
    ("2022-01-01", "2023-01-01"),
    ("2023-01-01", "2023-01-01"),
    ("2019-01-01", "2022-01-01"),
    ("2023-01-01", "2026-01-01"),
    ("2022-01-01", "2022-01-01")
]
_TEST1 = [YearRange(x[0], x[1]) for x in _TEST1_RAW]

def test_merge_year_ranges():
    assert merge_year_ranges(_TEST1) == [YearRange("2018-01-01", "2026-01-01")]