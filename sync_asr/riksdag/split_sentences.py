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
from sync_asr.ctm_edit import split_sentences, ctm_from_file, generate_filename, CTMEditLine
import argparse
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(description="""
    Extract sentences from directoy of ctmedit files
    """)
    parser.add_argument("rdapi_in",
                        type=Path,
                        help="""Directory containing ctmedit files.""")
    parser.add_argument("clean_dir",
                        type=Path,
                        help="""Directory to write clean(ed) sentences""")
    parser.add_argument("noisy_dir",
                        type=Path,
                        help="""Directory to write remaining sentences""")
    args = parser.parse_args()
    return args


def check_dir(dir: Path, verbose=False):
    if not dir.is_dir() and dir.exists():
        print(dir.name, "exists, but is not a directory. Exiting.")
        exit(1)
    elif not dir.exists():
        if verbose:
            print(dir.name, "does not exist; creating")
        dir.mkdir()


def check_correct(lines: CTMEditLine, acceptable=[]):
    for line in lines:
        if line.edit != "cor" or line.edit not in acceptable:
            return False
    return True


def preprocess_noop(lines):
    return lines


def main():
    args = get_args()

    # if args.rdapi_in and check_dir(args.rdapi_in):
    #     INDIR = args.rdapi_in
    # if args.clean_dir and check_dir(args.clean_dir):
    #     CLEANDIR = args.clean_dir
    # if args.noisy_dir and check_dir(args.noisy_dir):
    #     NOISYDIR = args.noisy_dir
    INDIR = args.rdapi_in
    CLEANDIR = args.clean_dir
    NOISYDIR = args.noisy_dir

    preprocess = preprocess_noop

    noisy = []
    for file in INDIR.glob("H*"):
        # if file.name == "H810255":
        #     continue
        noisy = []
        counter = 1
        lines = ctm_from_file(file)
        # lines = preprocess(lines)
        splits = split_sentences(lines)

        def write_noisy():
            outfile = NOISYDIR / f"{file.name}_{counter:04d}"
            with open(outfile, "w") as of:
                for line in noisy:
                    of.write(str(line) + "\n")

        for split in splits:
            if check_correct(split):
                fn = generate_filename(split)
                with open(CLEANDIR / fn, "w") as of:
                    for line in split:
                        of.write(str(line) + "\n")
                if noisy != []:
                    write_noisy()
                    counter += 1
                    noisy = []
            else:
                noisy += split
        if noisy != []:
            write_noisy()

if __name__ == '__main__':
        main()