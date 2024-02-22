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
import csv
import icu
import tarfile
import json
import io


FIELD_NAMES = [
    "orthography",
    "extended_pos",
    "morphology",
    "decomp",
    "decpos",
    "source",
    "language_code",
    "garbage",
    "domain",
    "abbr_acr",
    "expansion",
    "transliteration1",
    "certainty_trans_1",
    "status_trans_1",
    "language_code_trans_1",
    "transliteration2",
    "certainty_trans_2",
    "status_trans_2",
    "language_code_trans_2",
    "transliteration3",
    "certainty_trans_3",
    "status_trans_3",
    "language_code_trans_3",
    "transliteration4",
    "certainty_trans_4",
    "status_trans_4",
    "language_code_trans_4",
    "auto_gen_variants",
    "set_id",
    "set_name",
    "style_status",
    "inflector_role",
    "lemma",
    "inflection_rule",
    "morph_label",
    "compounder_code",
    "semantic_info",
    "available_field1",
    "available_field2",
    "available_field3",
    "available_field4",
    "available_field5",
    "available_field6",
    "available_field7",
    "available_field8",
    "available_field9",
    "frequency",
    "original_orthography",
    "comment_field",
    "update_info",
    "unique_id"
]

TRANSLIT = """
n\` → ɳ ;
s\` → ʂ ;
l\` → ɭ ;
t\` → ʈ ;
d\` → ɖ ;
A → ɑ ;
O → ɔ ;
I → ɪ ;
E \* U → e \u2040 ʊ ;
E → ɛ ;
U → ʊ ;
Y → ʏ ;
2 → ø ;
9 → ø ;
u 0 → ɵ ;
N → ŋ ;
'""' → ² ;
'"' → ˈ ;
\% → ˌ ;
\: → ː ;
\$ → \. ;
g → ɡ ;
s \\\' → ɕ ;
x \\\\ → ɧ ;
\* → \u2040 ;
"""

# !wget http://www.nb.no/sbfil/leksikalske_databaser/leksikon/sv.leksikon.tar.gz -O /tmp/sv.leksikon.tar.gz


with tarfile.open("/tmp/sv.leksikon.tar.gz") as tar:
    f = tar.extractfile("NST svensk leksikon/swe030224NST.pron/swe030224NST.pron")
    prondata = f.read()
    prondata = prondata.decode('latin1')


def transliterator_from_rules(name, rules):
    fromrules = icu.Transliterator.createFromRules(name, rules)
    icu.Transliterator.registerInstance(fromrules)
    return icu.Transliterator.createInstance(name)

swelex_trans = transliterator_from_rules("swelex_trans", TRANSLIT)

assert swelex_trans.transliterate('""bA:n`s`$%ma$man') == "²bɑːɳʂ.ˌma.man"
assert swelex_trans.transliterate('"b9r$mIN$ham') == "ˈbør.mɪŋ.ham"
assert swelex_trans.transliterate('"bI$rU') == "ˈbɪ.rʊ"
assert swelex_trans.transliterate('""bIsp$%go:$d`en') == "²bɪsp.ˌɡoː.ɖen"
assert swelex_trans.transliterate('"x\A:l') == "ˈɧɑːl"
assert swelex_trans.transliterate("\"s'u:$lens") == "ˈɕuː.lens"
assert swelex_trans.transliterate('a$"lE*U$te$n`a') == 'a.ˈle⁀ʊ.te.ɳa'
assert swelex_trans.transliterate('"fu0l') == 'ˈfɵl'

def collapse_available_fields(data):
    output = []
    for i in range(1, 10):
        if data[f"available_field{i}"] != "":
            output.append(data[f"available_field{i}"])
        del data[f"available_field{i}"]
    data["available_fields"] = output
    return data

def collapse_transliterations(data):
    output = []
    for i in range(1, 5):
        if data[f"transliteration{i}"] != "":
            tmp = {}
            tmp["transliteration"] = data[f"transliteration{i}"]
            tmp["ipa"] = swelex_trans.transliterate(data[f"transliteration{i}"])
            tmp["certainty"] = data[f"certainty_trans_{i}"]
            tmp["status"] = data[f"status_trans_{i}"]
            tmp["language_code"] = data[f"language_code_trans_{i}"]
            output.append(tmp)
        del data[f"transliteration{i}"]
        del data[f"certainty_trans_{i}"]
        del data[f"status_trans_{i}"]
        del data[f"language_code_trans_{i}"]
    data["transliterations"] = output
    return data

with open("svlex.json", "w") as outf:
    swelexf = io.StringIO(prondata)
    swelex = csv.DictReader(swelexf, delimiter=';', fieldnames=FIELD_NAMES, quoting=csv.QUOTE_NONE)
    for row in swelex:
        row["decomp"] = [f for f in row["decomp"].split("+") if f != ""]
        row = collapse_available_fields(row)
        row = collapse_transliterations(row)
        jsonstr = json.dumps(row)
        outf.write(jsonstr + "\n")
