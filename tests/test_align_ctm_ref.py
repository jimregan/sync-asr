# Copyright 2016    Vimal Manohar
#           2020    Dongji Gao
# Apache 2.0.
from sync_asr.kaldi.align_ctm_ref import smith_waterman_alignment


def test_smith_waterman_alignment():
    hyp = "GCCAT"
    ref = "AGCACACA"

    output, score = smith_waterman_alignment(
        ref, hyp, similarity_score_function=lambda x, y: 2 if (x == y) else -1,
        del_score=-1, ins_score=-1, eps_symbol="-", align_full_hyp=True)

    assert output == ""
