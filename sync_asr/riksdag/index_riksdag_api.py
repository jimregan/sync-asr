from pathlib import Path
import argparse
from .riksdag_api import RiksdagAPI, clean_text


def get_args():
    parser = argparse.ArgumentParser(description="""
    Convert a directory of Riksdag API output to Kaldi text format
    """)
    parser.add_argument('dir', type=str, help='directory containing API JSON')
    parser.add_argument('output', type=str, help='output file name')
    parser.add_argument('texttodoc', type=str, required=False,
        help="output file to write list of documents with their subdocuments")
    parser.add_argument('doctotext', type=str, required=False,
        help="output file to write list of subdocuments with their documents")
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
            text_to_doc["vidid"] = []
            if "speakers" not in doc:
                continue
            for pair in rdapi.get_paragraphs_with_ids():
                text = clean_text(pair["text"])
                if text == "":
                    continue
                text_to_doc["vidid"].append(pair["docid"])
                outf.write(f'{pair["docid"]} {text}\n')
    if args.texttodoc:
        with open(args.texttodoc, "w") as outf:
            for k in text_to_doc:
                outf.write(f'{k} {" ".join(text_to_doc[k])}\n')
    if args.doctotext:
        with open(args.doctotext, "w") as outf:
            for k in text_to_doc:
                for v in text_to_doc[k]:
                    outf.write(f'{v} {k}\n')


if __name__ == '__main__':
    main()
