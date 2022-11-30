# Copyright 2016    Vimal Manohar
#           2020    Dongji Gao
# Apache 2.0.
from sync_asr.kaldi.align_ctm_ref import smith_waterman_alignment


_EXP = [
    ('G', 'G', 1, 0, 2, 1),
    ('C', 'C', 2, 1, 3, 2),
    ('A', '-', 3, 2, 4, 2),
    ('C', 'C', 4, 2, 5, 3),
    ('A', 'A', 5, 3, 6, 4),
    ('C', 'T', 6, 4, 7, 5)
]


def test_smith_waterman_alignment():
    hyp = "GCCAT"
    ref = "AGCACACA"

    output, score = smith_waterman_alignment(
        ref, hyp, similarity_score_function=lambda x, y: 2 if (x == y) else -1,
        del_score=-1, ins_score=-1, eps_symbol="-", align_full_hyp=True)

    assert output == _EXP
    assert score == 6
