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
_CORRECTIONS = """
byggsenktionsavgiften byggsanktionsavgiften
här herr
vvi vi
prisposbeloppet prisbasbeloppet
"""


def get_corrections():
    return {k: v for k, v in (l.split() for l in _CORRECTIONS.split('\n') if l != "")}
