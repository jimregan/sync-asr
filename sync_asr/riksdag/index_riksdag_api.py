from pathlib import Path
import argparse
from .riksdag_api import RiksdagAPI, clean_text


def get_args():
    parser = argparse.ArgumentParser(description="""
    Convert a directory of Riksdag API output to Kaldi text format
    """)
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
    with open(args.output, "w") as outf:
        for file in API_OUTPUT.glob("*"):
            rdapi = read_api_json_file(file)
            if rdapi is None:
                continue
            doc = rdapi.videodata
            if "speakers" not in doc:
                continue
            for pair in rdapi.get_paragraphs_with_ids():
                text = clean_text(pair["text"])
                if text == "":
                    continue
                outf.write(f'{pair["docid"]} {text}\n')


if __name__ == '__main__':
    main()
