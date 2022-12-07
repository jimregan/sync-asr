_CORRECTIONS = """
byggsenktionsavgiften byggsanktionsavgiften
här herr
vvi vi
prisposbeloppet prisbasbeloppet
"""


def get_corrections():
    return {k: v for k, v in (l.split() for l in _CORRECTIONS.split('\n') if l != "")}
