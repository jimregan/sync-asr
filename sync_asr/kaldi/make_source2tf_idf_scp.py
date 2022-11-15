# https://github.com/kaldi-asr/kaldi/blob/cbed4ff688a172a7f765493d24771c1bd57dcd20/egs/wsj/s5/steps/cleanup/segment_long_utterances.sh#L311
# In the kaldi script, everything is based on a split by number of jobs
# We have a split based on document IDs.
from pathlib import Path
import sys

tdidf_dir = Path(sys.argv[1])

with open("source2tf_idf.scp", "w") as outfile:
    for file in tdidf_dir.glob("*"):
        stem = file.stem
        stem = stem.replace(".txt", "").replace("src_tf_idf.", "")
        outfile.write(f"{stem} {file}\n")