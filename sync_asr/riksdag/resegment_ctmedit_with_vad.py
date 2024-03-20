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
except ImportError:
    def main():
        exit(1)


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
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True)
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

    
    # get_speech_timestamps(data, model, sampling_rate=16_000)
    