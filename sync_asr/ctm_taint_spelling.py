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
from sync_asr.ctm_edit import CTMEditLine, merge_consecutive


class HunspellChecker():
    def __init__(self, dict, aff):
        self.dict = dict
        self.aff = aff
        self.speller = hunspell.HunSpell(dict, aff)

    def check(self, text):
        PUNCT = [".", ",", ":", ";", "!", "?", "-"]
        comp = text
        if comp[-1] in PUNCT:
            comp = comp[:-1]

        return self.speller.spell(comp)

    def check_pair(self, text, ref):
        if self.check(text) and not self.check(ref):
            return "correct_text"
        elif self.check(ref) and not self.check(text):
            return "correct_ref"
        elif self.check(ref) and self.check(text):
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
    parser.add_argument("--check-bigrams",
                        action='store_true',
                        default=False,
                        help="""Check for split compounds.""")
    parser.add_argument("--check-bigrams-ref",
                        action='store_true',
                        default=False,
                        help="""Check for split compounds, using a reliable reference""")
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


def check_bigrams(ctm_lines, speller, try_hyph=False, ref_only=True):
    def something_has_eps(a, b, ref_only=ref_only):
        if ref_only:
            return b.has_eps()
        else:
            return a.has_eps() or b.has_eps()
    
    def text_equals(a, b, eps='"<eps>"', ref_only=ref_only):
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
    if i == len(ctm_lines) - 2:
        output_ctm.append(ctm_lines[-1])
    return output_ctm


def main():
    args = get_args()
    speller = HunspellChecker(dict=args.dict_path, aff=args.aff_path)
    ctm_lines = []
    for line in args.ctm_edits_in.readlines():
        ctm_lines.append(CTMEditLine(line))
    if args.fix_case_difference:
        for item in ctm_lines:
            item.fix_case_difference()
    if args.check_bigrams:
        ctm_lines = check_bigrams(ctm_lines, speller)
    elif args.check_bigrams_ref:
        ctm_lines = check_bigrams(ctm_lines, speller, ref_only=True)
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
