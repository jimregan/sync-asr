try:
    import hunspell
except ImportError:
    print("Could not import hunspell")
    print("Hint: pip install hunspell")
    if __name__ == '__main__':
        quit()
    class HunspellChecker():
        pass

import argparse
from sync_asr.ctm_edit import CTMEditLine


class HunspellChecker():
    def __init__(self, dict, aff):
        self.dict = dict
        self.aff = aff
        self.speller = hunspell.HunSpell(dict, aff)

    def check(self, text):
        return self.speller.spell(text)

    def check_pair(self, text, ref):
        if self.speller.spell(text) and not self.speller.spell(ref):
            return "correct_text"
        elif self.speller.spell(ref) and not self.speller.spell(text):
            return "correct_ref"
        elif self.speller.spell(ref) and self.speller.spell(text):
            return "correct_both"
        else:
            return "incorrect_both"


def get_args():
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
    parser.add_argument("ctm_edits_in",
                        type=argparse.FileType('r'),
                        help="""Filename of input ctm-edits file.  Use
                        /dev/stdin for standard input.""")
    args = parser.parse_args()
    return args


def inline_check_unigram(ctm_lines, speller):
    for line in ctm_lines:
        if line.edit == "cor":
            if speller.check(line.text):
                continue
            else:
                line.set_prop("spelling", "incorrect_both")
        else:
            prop = speller.check_pair(line.text, line.ref)
            line.set_prop("spelling", prop)


def main():
    args = get_args()
    speller = HunspellChecker(dict=args.dict_path, aff=args.aff_path)
    ctm_lines = []
    for line in args.ctm_edits_in.readlines():
        ctm_lines.append(CTMEditLine(line))
    if args.fix_case_difference:
        for item in ctm_lines:
            item.fix_case_difference()
    inline_check_unigram(ctm_lines, speller)
    for item in ctm_lines:
        print(item)    


if __name__ == '__main__':
    if __package__ is None:
        from pathlib import Path
        import sys

        file = Path(__file__).resolve()
        parent, top = file.parent, file.parents[3]

        sys.path.append(str(top))
        try:
            sys.path.remove(str(parent))
        except ValueError: # Already removed
            pass

        import sync_asr
        __package__ = 'sync_asr'
    main()
