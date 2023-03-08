with open("test.tsv") as origf, open("test_new.tsv") as newf, open("test_filt.tsv", "w") as out:
    orig = []
    new = []
    for line in origf.readlines():
        parts = line.split("\t")
        orig.append(parts[0])
    for nline in newf.readlines():
        nline = nline.replace("/Users/joregan/Playing/", "/home/joregan/")
        parts = nline.split("\t")
        if parts[0] in orig:
            out.write(nline)
