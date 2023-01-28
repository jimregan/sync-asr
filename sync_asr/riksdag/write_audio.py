import pydub

CSV1_FIELDS = [
    "AudioID", "SpeakerID", "Name", "Condition", "Gender",
    "Duration (> 2 min)", "filename", "transcription1 (Whisper)",
    "transcription2 (KB)"
]

speakers = {}
speaker_counter = 1
line_count = 0

previous_speaker = ""
with open("segments.tsv") as segs:
    for line in segs.readlines():
        condition = 1
        line = line.strip()
        parts = line.split("\t")
        line_count += 1
        speaker = parts[0]
        if speaker not in speakers:
            speakers[speaker] = speaker_counter
            speaker_counter += 1
        else:
            condition = 2
        gender = "f" if parts[1].endswith("F") else "m"
        vidid = parts[2]
        start_time = int(parts[3])
        end_time = int(parts[4])
        text = parts[5]
        wav_name = f"sweterror-{speaker_counter:02d}-{condition}.wav"
        print(wav_name)
