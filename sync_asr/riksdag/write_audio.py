from pydub import AudioSegment
from pathlib import Path


CSV1_FIELDS = [
    "AudioID", "SpeakerID", "Name", "Condition", "Gender",
    "Duration (> 2 min)", "filename", "transcription1 (Whisper)",
    "transcription2 (KB)"
]
# CSV2_FIELDS = ["Type", "Segment", "Gender", "Year"]

speakers = {}
speaker_counter = 1
line_count = 0
parameters=["-ac", "1", "-acodec", "pcm_s16le", "-ar", "16000"]

previous_speaker = ""
with open("segments.tsv") as segs, open("segments_written.csv", "w") as outcsv:
    outcsv.write("\t".join(CSV1_FIELDS))
    outcsv.write("\n")
    for line in segs.readlines():
        condition = 1
        line = line.strip()
        parts = line.split("\t")
        line_count += 1
        speaker = parts[0]
        if speaker not in speakers:
            speakers[speaker] = speaker_counter
            current_speaker = speaker_counter
            speaker_counter += 1
        else:
            current_speaker = speakers[speaker]
            condition = 2
        gender = "f" if parts[1].endswith("F") else "m"
        type = "validation" if parts[1].startswith("VAL") else "test"
        vidid = parts[2]
        start_time = int(parts[3])
        end_time = int(parts[4])
        duration = (end_time - start_time) / 1000
        text = parts[5]
        audio_id = f"{current_speaker:02d}-{condition}"
        wav_name = f"sweterror-{audio_id}.wav"
        video_name = f"/sbtal/riksdag-video/{vidid}_480p.mp4"
        temp_wav = f"/tmp/{vidid}.wav"
        if not Path(temp_wav).exists():
            vid_as = AudioSegment.from_file(video_name, "mp4")
            vid_as.export(temp_wav, format="wav", parameters=parameters)
        wav_as = AudioSegment.from_wav(temp_wav)
        cut = wav_as[start_time:end_time]
        cut.export(wav_name, format="wav", parameters=parameters)
        csv_name = wav_name.replace(".wav", "-w.csv")
        with open(csv_name, "w") as segcsv:
            segcsv.write("Speaker ID\tVideo ID\tTranscript\n")
            segcsv.write(f"{current_speaker:02d}\t{vidid}\t{text}\n")
        outcsv.write(f"{audio_id}\t{current_speaker:02d}\t{speaker}\t{condition}\t")
        outcsv.write(f"{gender}\t{duration}\t{wav_name}\t{csv_name}\t-\n")
        
