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
from sync_asr.ctm_edit import (
    all_correct,
    clean_text,
    ctm_from_file,
    generate_filename,
    split_sentences,
)
from sync_asr.riksdag.corrections import get_corrections
import argparse
from pathlib import Path
from string import punctuation

try:
    from num2words import num2words
except ImportError:
    def num2words(num, to=None, lang=None):
        print("num2words not available")
        exit(1)


PUNCT = set(punctuation)

CONJUNCTIONS = ["men", "och", "eller", "så"]


def get_args():
    parser = argparse.ArgumentParser(description="""
    Extract sentences from directory of ctmedit files
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
    parser.add_argument("--run-stage",
                        type=str,
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


def preprocess_noop(lines):
    return lines


def compare_text(a, b, lc=False):
    word = clean_text(b)
    if a == word:
        return True
    if lc and a == word.lower():
        return True
    return False


def preprocess_fix_corrections(lines):
    corrections = get_corrections()
    def checker(a, b):
        if compare_text(a, b, True):
            return True
        word = clean_text(b)
        if a in corrections and word in corrections[a]:
            return True
        if a in corrections and word.lower() in corrections[a]:
            return True
        return False

    for line in lines:
        line.mark_correct_from_function(checker, make_equal=False)

    return lines


def preprocess_num2words(lines):
    def checker(a, b):
        word = clean_text(b)
        try:
            num = int(word)
            card = num2words(num, to="cardinal", lang="sv")
            if a == card:
                return True
            ord = num2words(num, to="ordinal", lang="sv")
            if a == ord:
                return True
        except ValueError:
            return False
        return False

    for line in lines:
        line.mark_correct_from_function(checker, make_equal=False)

    return lines


def preprocess_abbrev(lines):
    PREFIXES = []
    with open("prefixes.tsv") as f:
        for line in f.readlines():
            parts = line.strip().split()
            PREFIXES.append((parts[0], f"{parts[1]}-"))

    def checker(a, b):
        word = clean_text(b)
        for pfx in PREFIXES:
            if a == pfx[0] and b == pfx[1].replace("-", ""):
                return True
            if a.startswith(pfx[0]) and b.startswith(pfx[1]):
                if a[len(pfx[0]):] == b[len(pfx[1]):]:
                    return True
        return False

    for line in lines:
        line.mark_correct_from_function(checker, make_equal=False)

    return lines


def preprocess_merge_eps(ctmedits):
    i = 0

    SUBS = get_corrections()
    def is_subst(ta, tb, lc=False):
        if ta in SUBS:
            if tb in SUBS[ta]:
                return True
            elif lc and tb.lower() in SUBS[ta]:
                return True
        return False

    while i < len(ctmedits):
        window = ctmedits[i:i+2]
        if len(window) == 2:
            a = window[0]
            b = window[1]
            if a.text == b.get_ref(True) or is_subst(a.text, b.get_ref(True, False)):
                if a.ref_eps():
                    a.ref = b.ref
                    b.ref = "<eps>"
                    a.edit = "cor"
                    b.edit = "ins"
                if b.text in CONJUNCTIONS:
                    b.edit = "ins-conj"
            elif a.text_eps():
                if a.ref + b.ref == b.text:
                    b.text = b.ref = f"{a.ref}_{b.ref}"
                    b.edit = "cor"
                    a.nullify()
            elif a.text + b.text == a.get_ref(True) and b.ref == "<eps>":
                #b.text = b.ref = a.ref
                b.ref = a.ref
                b.edit = "cor"
                b.reset_start(a.start_time)
                a.nullify()
            elif a.text + b.ref == b.get_ref(True) and a.ref == "<eps>":
                #b.text = b.ref
                b.edit = "cor"
                b.reset_start(a.start_time)
                a.nullify()
        i += 1
    return ctmedits


def main():
    args = get_args()

    RD_PROCESSING_STAGES = {
        "one": preprocess_noop,
        "two": preprocess_fix_corrections,
        "three": preprocess_num2words,
        "four": preprocess_abbrev,
        "five": preprocess_merge_eps,
        "six": preprocess_merge_eps,
    }
    RD_USE_CONJUNCTIONS = [
        "six",
    ]

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

    if args.run_stage and args.run_stage in RD_PROCESSING_STAGES:
        preprocess = RD_PROCESSING_STAGES[args.run_stage]
    if args.run_stage and args.run_stage in RD_USE_CONJUNCTIONS:
        inner_all_correct = lambda x: all_correct(x, CONJUNCTIONS)
    else:
        inner_all_correct = lambda x: all_correct(x)

    noisy = []
    for file in INDIR.glob("H*"):
        # if file.name == "H810255":
        #     continue
        noisy = []
        counter = 1
        lines = ctm_from_file(file)
        lines = preprocess(lines)
        splits = split_sentences(lines, CONJUNCTIONS)

        def write_noisy():
            outfile = NOISYDIR / f"{file.name}_{counter:04d}"
            with open(outfile, "w") as of:
                for line in noisy:
                    of.write(str(line) + "\n")

        for split in splits:
            if inner_all_correct(split):
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