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
from typing import List
from .ctm_edit import CTMEditLine


try:
    import hunspell
except ImportError:
    print("Could not import hunspell")
    print("Hint: pip install hunspell")
    if __name__ == '__main__':
        quit()


    class HunspellChecker():
        pass


try:
    import editdistance
except ImportError:
    print("Could not import editdistance")
    print("Hint: pip install editdistance")
    if __name__ == '__main__':
        quit()


import argparse
from .ctm_edit import CTMEditLine, merge_consecutive


class HunspellChecker():
    """
    Class to encapsulate a Hunspell spell checker

    :param str dict: Path to the dictionary to use
    :param str aff: Path to the dictionary's affix file
    """
    def __init__(self, dict: str, aff: str):
        """
        Constructor method
        """
        self.dict = dict
        self.aff = aff
        self.speller = hunspell.HunSpell(dict, aff)

    def check(self, text: str) -> bool:
        """
        Check spelling using the Hunspell checker.

        :param str text: the word to check
        :return: True if correctly spelled
        """
        PUNCT = [".", ",", ":", ";", "!", "?", "-"]
        comp = text
        if comp[-1] in PUNCT:
            comp = comp[:-1]

        return self.speller.spell(comp)

    def check_pair(self, text: str, ref: str) -> str:
        """
        Check a pair of spellings, typically corresponding to
        a hypothesis from an ASR system, and a reference text

        :param str text: text to check, typically from ASR output
        :param str ref: text to check, typically reference text
        :return: string representing the results of both checks:
            | "correct_text" if only text is correct
            | "correct_ref" if only ref is correct
            | "correct_both" if both are correct
            | "incorrect_both" if both are incorrect
        """
        if self.check(text) and not self.check(ref):
            return "correct_text"
        elif self.check(ref) and not self.check(text):
            return "correct_ref"
        elif self.check(ref) and self.check(text):
            return "correct_both"
        else:
            return "incorrect_both"


def get_args():
    """
    Get arguments for command line interface
    """
    parser = argparse.ArgumentParser(
        """Checks a CTMEdit file for spelling errors""")

    parser.add_argument("--dict-path",
                        type=str,
                        default="/usr/share/hunspell/sv_SE.dic",
                        help="""Path to the Hunspell dictionary to use""")
    parser.add_argument("--aff-path",
                        type=str,
                        default="/usr/share/hunspell/sv_SE.aff",
                        help="""Path to the Hunspell affix file to use""")
    parser.add_argument("--fix-case-difference",
                        action='store_true',
                        default=False,
                        help="""First check case/punctuation differences.""")
    parser.add_argument("--check-bigrams",
                        action='store_true',
                        default=False,
                        help="""Check for split compounds.""")
    parser.add_argument("--check-bigrams-ref",
                        action='store_true',
                        default=False,
                        help="""Check for split compounds, using a reliable reference""")
    parser.add_argument("--apply-changes",
                        action='store_true',
                        default=False,
                        help="""Apply spelling fixes instead of issuing warnings""")
    parser.add_argument("--max-edit-distance",
                        type=int,
                        default=1,
                        help="""Do not consider edit distance greater than this number in automatic application""")
    parser.add_argument("--edit-distance-percent",
                        type=float,
                        default=0.1,
                        help="""Percent of length of reference word""")
    parser.add_argument("--confusion-pairs",
                        type=argparse.FileType('r'),
                        required=False,
                        help="""Name of file containing confusion pairs to apply.""")
    parser.add_argument("ctm_edits_in",
                        type=argparse.FileType('r'),
                        help="""Filename of input ctm-edits file.  Use
                        /dev/stdin for standard input.""")
    args = parser.parse_args()
    return args


def inline_check_unigram(ctm_lines: List[CTMEditLine], speller: HunspellChecker):
    """
    Check individual words in a list of CTMEditLine for spelling errors.
    Operates inline (no return value)

    :param ctm_lines: a list of CTMEditLine to check
    :param speller: the spell checker to use
    """
    for line in ctm_lines:
        if line.edit == "cor":
            if speller.check(line.text):
                continue
            else:
                line.set_prop("spelling", "incorrect_both")
        else:
            prop = speller.check_pair(line.text, line.ref)
            line.set_prop("spelling", prop)


def check_bigrams(ctm_lines: List[CTMEditLine],
                  speller: HunspellChecker,
                  try_hyph=False, ref_only=True):
    def something_has_eps(a, b, ref_only=ref_only):
        if ref_only:
            return b.has_eps()
        else:
            return a.has_eps() or b.has_eps()
    
    def text_equals(a, b, eps="<eps>", ref_only=ref_only):
        text = "".join([a.text, b.text])
        ref = "".join([a.ref, b.ref])
        if ref_only:
            return text == ref.replace(eps, "")
        else:
            return text.replace(eps, "") == ref.replace(eps, "")

    output_ctm = []
    i = 0
    while i < len(ctm_lines)-1:
        pair = ctm_lines[i:i+2]

        text = "".join([pair[0].text, pair[1].text])
        if try_hyph:
            text_hyph = "-".join([pair[0].text, pair[1].text])
        ref = "".join([pair[0].ref, pair[1].ref])
        if try_hyph:
            ref_hyph = "-".join([pair[0].ref, pair[1].ref])

        if something_has_eps(pair[0], pair[1]) and text_equals(pair[0], pair[1]):
            if speller.check(text):
                new = merge_consecutive(pair[0], pair[1], text=text)
                output_ctm.append(new)
                i += 1
            elif try_hyph and speller.check(text_hyph):
                new = merge_consecutive(pair[0], pair[1], text=text_hyph)
                output_ctm.append(new)
                i += 1
            elif speller.check(ref):
                new = merge_consecutive(pair[0], pair[1], text=ref)
                output_ctm.append(new)
                i += 1
            elif try_hyph and speller.check(ref_hyph):
                new = merge_consecutive(pair[0], pair[1], text=ref_hyph)
                output_ctm.append(new)
                i += 1
            else:
                output_ctm.append(ctm_lines[i])
        else:
            output_ctm.append(ctm_lines[i])
        i += 1
    if i == len(ctm_lines) - 1:
        output_ctm.append(ctm_lines[-1])
    return output_ctm


def read_confusion_pairs(file):
    """
    Read a list of confusion pairs (confusable words) from a file
    """
    pairs = {}
    for line in file.readlines():
        k, v = line.split()
        if k not in pairs:
            pairs[k] = dict()
        pairs[k].append(v)
    if file is not None:
        file.close()
    return pairs


def post_process(ctm_lines, max_ed=1, ed_percent=0.1):
    for ctm_line in ctm_lines:
        if ctm_line.has_eps():
            ctm_line.delete_props()
            continue
        if ctm_line.get_prop("spelling") == "correct_both":
            ctm_line.delete_props()
            continue
        reflen = len(ctm_line.ref)
        if ctm_line.get_prop("spelling") == "correct_ref":
            ed = editdistance.eval(ctm_line.text, ctm_line.ref.lower())
            if ed < max(max_ed, reflen * ed_percent):
                ctm_line.set_correct_ref()
        ctm_line.delete_props()


def main():
    args = get_args()
    if args.confusion_pairs:
        pairs = read_confusion_pairs(args.confusion_pairs)
    speller = HunspellChecker(dict=args.dict_path, aff=args.aff_path)
    ctm_lines = []
    for line in args.ctm_edits_in.readlines():
        ctmedit = CTMEditLine(line)
        if args.confusion_pairs:
            ctmedit.mark_correct_from_list(pairs)
        ctm_lines.append(ctmedit)
    if args.fix_case_difference:
        for item in ctm_lines:
            item.fix_case_difference()
    if args.check_bigrams:
        ctm_lines = check_bigrams(ctm_lines, speller)
    elif args.check_bigrams_ref:
        ctm_lines = check_bigrams(ctm_lines, speller, ref_only=True)
    inline_check_unigram(ctm_lines, speller)
    if args.apply_changes:
        post_process(ctm_lines, args.max_edit_distance, args.edit_distance_percent)
    for item in ctm_lines:
        print(item)    


if __name__ == '__main__':
    main()
