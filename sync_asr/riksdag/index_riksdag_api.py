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
from pathlib import Path
import argparse
from .riksdag_api import RiksdagAPI, clean_text


def get_args():
    parser = argparse.ArgumentParser(description="""
    Convert a directory of Riksdag API output to Kaldi text format
    """)
    parser.add_argument('--text-to-doc', '-t', type=str, required=False,
        help="output file to write list of documents with their subdocuments")
    parser.add_argument('--doc-to-text', '-d', type=str, required=False,
        help="output file to write list of subdocuments with their documents")
    parser.add_argument('dir', type=str, help='directory containing API JSON')
    parser.add_argument('output', type=str, help='output file name')
    args = parser.parse_args()

    return args


def read_api_json_file(filename):
    infile = str(filename)
    return RiksdagAPI(filename=filename, nullify=True)


def main():
    args = get_args()
    API_OUTPUT = Path(args.dir)
    text_to_doc = {}
    with open(args.output, "w") as outf:
        for file in API_OUTPUT.glob("*"):
            rdapi = read_api_json_file(file)
            if rdapi is None:
                continue
            doc = rdapi.videodata
            vidid = rdapi.get_vidid()
            text_to_doc[vidid] = []
            if "speakers" not in doc:
                continue
            for pair in rdapi.get_paragraphs_with_ids():
                text = clean_text(pair["text"])
                if text == "":
                    continue
                text_to_doc[vidid].append(pair["docid"])
                outf.write(f'{pair["docid"]} {text}\n')
    if args.text_to_doc:
        with open(args.text_to_doc, "w") as outf:
            for k in text_to_doc:
                outf.write(f'{k} {" ".join(text_to_doc[k])}\n')
    if args.doc_to_text:
        with open(args.doc_to_text, "w") as outf:
            for k in text_to_doc:
                for v in text_to_doc[k]:
                    outf.write(f'{v} {k}\n')


if __name__ == '__main__':
    main()
