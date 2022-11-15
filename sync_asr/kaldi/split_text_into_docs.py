# Based on split_text_into_docs.pl
# Copyright 2017  Vimal Manohar
# Apache 2.0.
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="""
    Splits text into utterances that do not exceed `max-words`,
    where `text` contains an identifier as the first "word" of
    each line:
    `docs` contains the split text, with new identifiers,
    `doc2text` contains a mapping of the original identifiers to
    the new identifiers in `docs`.
    This implementation optionally takes an extra option, `text2doc`,
    to avoid requiring an additional script to create this file (the
    inverse of `doc2text`)
    """)
    parser.add_argument('TEXT', type=argparse.FileType('r'),
        help='input file containing utterance ids and text')
    parser.add_argument('DOC2TEXT', type=argparse.FileType('w'),
        help='output file containing mapping of documents to text files')
    parser.add_argument('DOCS', type=argparse.FileType('w'),
        help='output file containing documents')
    parser.add_argument('TEXT2DOC', nargs='?', type=argparse.FileType('w'),
        help='output file containing mapping of text files to documents')
    parser.add_argument('--max-words',
        help='Maximum number of words to consider', type=int, default=1000)
    args = parser.parse_args()

    return args


def _local_min(a, b):
    if a > b:
        return a
    else:
        return b


def run(args):
    for line in args.TEXT:
        line = line.strip()
        parts = line.split()
        utt = parts[0]
        parts = parts[1:]
        num_words = len(parts)

        if num_words <= args.max_words:
            print(line, file=args.DOCS)
            print(f"{utt} {utt}", file=args.DOC2TEXT)
            if args.TEXT2DOC is not None:
                print(f"{utt} {utt}", file=args.TEXT2DOC)
            continue
        
        num_docs = int(num_words / args.max_words) + 1
        num_words_shift = int(num_words / num_docs) + 1
        words_per_doc = num_words_shift

        for i in range(0, num_docs):
            st = i * num_words_shift
            end = _local_min(st + words_per_doc, num_words) - 1
            print(f"{utt}-{i} {' '.join(parts[st:end])}", file=args.DOCS)
            print(f"{utt}-{i} {utt}", file=args.DOC2TEXT)
            if args.TEXT2DOC is not None:
                print(f"{utt} {utt}-{i}", file=args.TEXT2DOC)


def main():
    args = get_args()
    try:
        run(args)
    finally:
        for f in [args.TEXT, args.DOC2TEXT, args.DOCS]:
            f.close()


if __name__ == '__main__':
    main()