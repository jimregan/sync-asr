import json
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="""
    Simple script to convert HuggingFace timestamped JSON to CTM.
    """)
    parser.add_argument('files', type=str, nargs='+', help='files to process')
    parser.add_argument('--lower', help='lowercase words', action='store_true', default=True)
    parser.add_argument('--riksdag', help='Riksdag-specific fixes', action='store_true', default=True)
    args = parser.parse_args()

    return args


def read_hfjson(json_file, lowercase=True, riksdag=False):
    with open(json_file) as jsonf:
        utt = json_file.split("/")[-1].replace(".json", "")
        if riksdag:
            utt = utt.replace("_480p", "")
        data = json.load(jsonf)
        if not "chunks" in data:
            raise ValueError(f"File does not appear to contain HuggingFace JSON")
        # utt_id channel_num start_time duration phone_id confidence
        ctm_lines = []
        for chunk in data["chunks"]:
            word = chunk["text"] if not lowercase else chunk["text"].lower()
            start = chunk["timestamp"][0]
            dur = chunk["timestamp"][1] - chunk["timestamp"][0]
            ctm_lines.append(f"{utt} 1 {start} {dur} {word} 1.0")
        return ctm_lines


def read_hfjson_write_ctm(json_file, lowercase=True, riksdag=False):
    ctm_lines = read_hfjson(json_file, lowercase, riksdag)
    outname = json_file.replace(".json", ".ctm")
    with open(outname, "w") as outf:
        for line in ctm_lines:
            outf.write(f"{line}\n")


def main():
    args = get_args()
    lc = args.lower
    for file in args.files:
        read_hfjson_write_ctm(file, lc)


if __name__ == '__main__':
    main()
