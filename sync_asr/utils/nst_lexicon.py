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
import tarfile
import json
import io
import requests

try:
    import icu
except ImportError:
    def get_transliterator():
        return None
    def transliterator_from_rules(name, rules):
        return None
    def get_nst_lexicon():
        return None


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
\} → ʉ ;
"""


def transliterator_from_rules(name, rules):
    fromrules = icu.Transliterator.createFromRules(name, rules)
    icu.Transliterator.registerInstance(fromrules)
    return icu.Transliterator.createInstance(name)


def _get_and_extract_csv_text():
    _URL = "http://www.nb.no/sbfil/leksikalske_databaser/leksikon/sv.leksikon.tar.gz"
    req = requests.get(_URL)
    assert req.status_code == 200, "Error downloading tar file"
    bytes = io.BytesIO(req.content)
    tar = tarfile.open(fileobj=bytes, mode='r:gz')
    f = tar.extractfile("NST svensk leksikon/swe030224NST.pron/swe030224NST.pron")
    prondata = f.read()
    prondata = prondata.decode('latin1')
    return prondata


def get_transliterator():
    swelex_trans = transliterator_from_rules("swelex_trans", TRANSLIT)
    return swelex_trans


def _check_transliterator(transliterator):
    try:
        assert transliterator.transliterate('""bA:n`s`$%ma$man') == "²bɑːɳʂ.ˌma.man"
        assert transliterator.transliterate('"b9r$mIN$ham') == "ˈbør.mɪŋ.ham"
        assert transliterator.transliterate('"bI$rU') == "ˈbɪ.rʊ"
        assert transliterator.transliterate('""bIsp$%go:$d`en') == "²bɪsp.ˌɡoː.ɖen"
        assert transliterator.transliterate('"x\A:l') == "ˈɧɑːl"
        assert transliterator.transliterate("\"s'u:$lens") == "ˈɕuː.lens"
        assert transliterator.transliterate('a$"lE*U$te$n`a') == 'a.ˈle⁀ʊ.te.ɳa'
        assert transliterator.transliterate('"fu0l') == 'ˈfɵl'
    except:
        return False
    return True


def _collapse_available_fields(data):
    output = []
    for i in range(1, 10):
        if data[f"available_field{i}"] != "":
            output.append(data[f"available_field{i}"])
        del data[f"available_field{i}"]
    data["available_fields"] = output
    return data


def _collapse_transliterations(data, transliterator):
    output = []
    for i in range(1, 5):
        if data[f"transliteration{i}"] != "":
            tmp = {}
            tmp["transliteration"] = data[f"transliteration{i}"]
            tmp["ipa"] = transliterator.transliterate(data[f"transliteration{i}"])
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


def _get_nst_lexicon_from_csv(prondata, transliterator):
    lexicon = []
    swelexf = io.StringIO(prondata)
    swelex = csv.DictReader(swelexf, delimiter=';', fieldnames=FIELD_NAMES, quoting=csv.QUOTE_NONE)
    for row in swelex:
        row["decomp"] = [f for f in row["decomp"].split("+") if f != ""]
        row = _collapse_available_fields(row)
        row = _collapse_transliterations(row, transliterator)
        lexicon.append(row)
    return lexicon


def get_nst_lexicon():
    transliterator = get_transliterator()
    prondata = _get_and_extract_csv_text()
    lexicon = _get_nst_lexicon_from_csv(prondata, transliterator)
    return lexicon
