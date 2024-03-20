# Copyright (c) 2024, Jim O'Regan for Språkbanken Tal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import io
import argparse
from pathlib import Path
from sync_asr.ctm_edit import ctm_from_file
try:
    from pydub import AudioSegment
    import torch
    import soundfile as sf
    from transformers import pipeline
    from datasets import Dataset
except ImportError:
    def main():
        exit(1)


PARAMS=["-ac", "1", "-acodec", "pcm_s16le", "-ar", "16000"]


def get_args():
    parser = argparse.ArgumentParser(description="""
    Resegment merged segments using VAD + rerunning a
    huggingface wav2vec2 model over the split sections.
    (To handle the relatively common case that longer
    silences were ignored.)
    """)
    parser.add_argument("ctmedit_dir",
                        type=Path,
                        help="Directory containing the ctmedit files")
    parser.add_argument("audio_dir",
                        type=Path,
                        help="Directory containing the audio files")
    parser.add_argument("audio_tmp",
                        type=Path,
                        help="Directory to hold audio converted to wav")
    parser.add_argument("--extension",
                        type=str,
                        default="wav",
                        help="Audio file extension")
    parser.add_argument("--model",
                        type=str,
                        help="Huggingface model ID")


def audiosegment_to_sf(seg: AudioSegment):
    return sf.read(io.BytesIO(seg.raw_data), format="RAW", subtype="PCM_16", samplerate=16000, channels=1)


def ctmlines_are_resegmentable(lines):
    if len(lines) != 2:
        return False
    if lines[0].text_eps():
        return lines[0].text == lines[0].ref + lines[1].ref
    elif lines[1].text_eps():
        return lines[1].text == lines[0].ref + lines[1].ref
    else:
        return False


def main():
    args = get_args()

    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True)
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

    pipe = pipeline(model=args.model)

    def process(segment):
        data, sr = audiosegment_to_sf(segment)
        audio_ds_input = []
        for i, ts in enumerate(get_speech_timestamps(data, model, sampling_rate=sr)):
            piece, piece_sr = audiosegment_to_sf(segment[ts["start"]:ts["end"]])
            audio_ds_input.append({
                "path": f"/fake/path/to/file.{i:03d}",
                "array": piece,
                "sampling_rate": piece_sr
            })
        ds = Dataset.from_dict({"audio": audio_ds_input})
        output = pipe(ds, return_timestamps="word")
        return output

    for file in args.ctmedit_dir.glob("*.ctmedit"):
        ctmedits = ctm_from_file(file)
        audiofile = ctmedits[0].id + "." + args.extension
        wavfile = ctmedits[0].id + ".wav"
        wavpath = args.audio_tmp / wavfile
        if not wavpath.exists():
            audiopath = args.audio_dir / audiofile
            if not audiopath.exists():
                continue
            audio = AudioSegment.from_file(str(file), args.extension)
            audio.export(str(wavpath), format="wav", parameters=PARAMS)
        audio = AudioSegment.from_wav(str(wavpath))

        processed = []
        i = 0
        while i < len(ctmedits):
            window = ctmedits[i:i+2]
            if ctmlines_are_resegmentable(window):
                # relevant = window[0] if not window[0].text_eps() else window[1]
                segment = audio[window[0].start_time:window[1].end_time]
                hf_json = process(segment)
                print(hf_json)
            else:
                processed.append(ctmedits[i])
            i += 1

if __name__ == '__main__':
    main()
