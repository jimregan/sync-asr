from .filter_vtt_to_speaker_list import FilteredSegment, subsplit_segment_list

current = []
output = []
if __name__ == '__main__':
    with open("/Users/joregan/Playing/sync_asr/rdfilt2") as inf:
        for line in inf.readlines():
            line = line.strip()
            if line == "":
                if current == []:
                    continue
                output += subsplit_segment_list(current)
                current = []
            else:
                parts = line.split("\t")
                fs = FilteredSegment(parts[0], parts[1], parts[2], int(parts[3]), int(parts[4]), parts[5])
                current.append(fs)

    for res in output:
        print(res)
