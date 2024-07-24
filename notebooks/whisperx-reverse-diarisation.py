# %%
import torch
if torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

# %%
from whisperx.diarize import DiarizationPipeline

# %%
from pathlib import Path
HF_DIR = Path.home() / ".huggingface"
HF_TOKEN = HF_DIR / "token"
TOKEN = ""
if HF_DIR.is_dir() and HF_TOKEN.exists():
    with open(str(HF_TOKEN)) as hf_tok:
        TOKEN = hf_tok.read().strip()

# %%
diar_pipe = DiarizationPipeline(use_auth_token=TOKEN, device=DEVICE)

# %%
AUDIO_PATH = Path("/home/joregan/hsi/audio")
MFA_DIR = "/home/joregan/hsi_mfa"
TSV_DIR = "/home/joregan/hsi_segments"
EG = AUDIO_PATH / "hsi_3_0715_227_001_inter-002.wav"

# %% [markdown]
# This next part is just to confirm that the output of `merge_chunks` is similar in terms of timestamps to the diarisation output

# %%
# from whisperx.vad import load_vad_model, merge_chunks
# from whisperx.audio import load_audio, SAMPLE_RATE

# # https://github.com/m-bain/whisperX/blob/58f00339af7dcc9705ef49d97a1f40764b7cf555/whisperx/asr.py#L336
# default_vad_options = {
#     "vad_onset": 0.500,
#     "vad_offset": 0.363
# }

# audio = load_audio(str(EG))

# chunk_size = 30

# # https://github.com/m-bain/whisperX/blob/58f00339af7dcc9705ef49d97a1f40764b7cf555/whisperx/asr.py#L186
# vad_model = load_vad_model(torch.device(DEVICE), use_auth_token=None, **default_vad_options)
# vad_segments = vad_model({"waveform": torch.from_numpy(audio).unsqueeze(0), "sample_rate": SAMPLE_RATE})
# vad_segments = merge_chunks(
#     vad_segments,
#     chunk_size,
#     onset=default_vad_options["vad_onset"],
#     offset=default_vad_options["vad_offset"],
# )

# %%
# vad_segments[0]

# %%
def get_diarised_chunks(filename):
    diar_res = diar_pipe(filename, num_speakers=2)
    res = []
    for idx, diar_seg in diar_res.iterrows():
        res.append({
            "start": diar_seg["start"],
            "end": diar_seg["end"],
            "segments": [(diar_seg["start"], diar_seg["end"])],
            "speaker": diar_seg["speaker"]
        })
    return res

# %%
import wave
import numpy as np

def write_wave(filename, data):
    data_denorm = data * 32768.0
    data16 = data_denorm.astype(np.int16)
    output = wave.open(filename, "w")
    # pcm_s16le, single channel
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(16000)
    output.writeframes(data16.tobytes())
    output.close()

# %%
# just for my reference
_FORMATS = """
hsi_N_NNNN_NNN_NNN-mic.wav
hsi_N_NNNN_NNN_NNN-micN-NNN.wav
hsi_N_NNNN_NNN_NNN_NNN_inter.wav
hsi_N_NNNN_NNN_NNN_NNN_main.wav
hsi_N_NNNN_NNN_NNN_inter.wav
hsi_N_NNNN_NNN_NNN_main.wav
hsi_N_NNNN_NNN_inter.wav
hsi_N_NNNN_NNN_main.wav
"""
def get_speaker_id(filename, detected_speaker):
    detected_speaker = detected_speaker.replace("SPEAKER_", "")
    if "inter" in filename or "mic2" in filename:
        part = "inter"
    elif "main" in filename or "mic1" in filename:
        part = "main"
    elif filename.endswith("-mic.wav"):
        # one file
        part = "inter"
    pieces = filename.split("_")
    return f"hsi_{pieces[1]}_{part}_{detected_speaker}"

# %%
def ensure_directory(speaker_id, base_dir="/home/joregan/hsi_mfa"):
    base_path = Path(base_dir)
    if not base_path.is_dir():
        base_path.mkdir()
    speaker_path = base_path / speaker_id
    if not speaker_path.is_dir():
        speaker_path.mkdir()

# %%
import numpy as np
from whisperx.types import TranscriptionResult
from typing import List, Union
import faster_whisper
from whisperx.asr import find_numeral_symbol_tokens, SingleSegment

# https://github.com/m-bain/whisperX/blob/58f00339af7dcc9705ef49d97a1f40764b7cf555/whisperx/asr.py#L173
def transcribe(
    self, audio: Union[str, np.ndarray], batch_size=None, num_workers=0, language=None, task=None, chunk_size=30, print_progress = False, combined_progress=False
) -> TranscriptionResult:
    filename = audio
    if isinstance(audio, str):
        audio = load_audio(audio)

    def data(audio, segments):
        for seg in segments:
            f1 = int(seg['start'] * SAMPLE_RATE)
            f2 = int(seg['end'] * SAMPLE_RATE)
            if (seg['end'] - seg['start']) < 30.0:
                yield {'inputs': audio[f1:f2]}

    # vad_segments = self.vad_model({"waveform": torch.from_numpy(audio).unsqueeze(0), "sample_rate": SAMPLE_RATE})
    # vad_segments = merge_chunks(
    #     vad_segments,
    #     chunk_size,
    #     onset=self._vad_params["vad_onset"],
    #     offset=self._vad_params["vad_offset"],
    # )
    vad_segments = get_diarised_chunks(filename)
    if self.tokenizer is None:
        language = language or self.detect_language(audio)
        task = task or "transcribe"
        self.tokenizer = faster_whisper.tokenizer.Tokenizer(self.model.hf_tokenizer,
                                                            self.model.model.is_multilingual, task=task,
                                                            language=language)
    else:
        language = language or self.tokenizer.language_code
        task = task or self.tokenizer.task
        if task != self.tokenizer.task or language != self.tokenizer.language_code:
            self.tokenizer = faster_whisper.tokenizer.Tokenizer(self.model.hf_tokenizer,
                                                                self.model.model.is_multilingual, task=task,
                                                                language=language)
            
    if self.suppress_numerals:
        previous_suppress_tokens = self.options.suppress_tokens
        numeral_symbol_tokens = find_numeral_symbol_tokens(self.tokenizer)
        print(f"Suppressing numeral and symbol tokens")
        new_suppressed_tokens = numeral_symbol_tokens + self.options.suppress_tokens
        new_suppressed_tokens = list(set(new_suppressed_tokens))
        self.options = self.options._replace(suppress_tokens=new_suppressed_tokens)

    segments: List[SingleSegment] = []
    batch_size = batch_size or self._batch_size
    total_segments = len(vad_segments)
    for idx, out in enumerate(self.__call__(data(audio, vad_segments), batch_size=batch_size, num_workers=num_workers)):
        if print_progress:
            base_progress = ((idx + 1) / total_segments) * 100
            percent_complete = base_progress / 2 if combined_progress else base_progress
            print(f"Progress: {percent_complete:.2f}%...")
        text = out['text']
        if batch_size in [0, 1, None]:
            text = text[0]
        segments.append(
            {
                "text": text,
                "start": round(vad_segments[idx]['start'], 3),
                "end": round(vad_segments[idx]['end'], 3),
                "speaker": vad_segments[idx]['speaker']
            }
        )

    # revert the tokenizer if multilingual inference is enabled
    if self.preset_language is None:
        self.tokenizer = None

    # revert suppressed tokens if suppress_numerals is enabled
    if self.suppress_numerals:
        self.options = self.options._replace(suppress_tokens=previous_suppress_tokens)

    return {"segments": segments, "language": language}


# %%
# https://github.com/m-bain/whisperX/blob/58f00339af7dcc9705ef49d97a1f40764b7cf555/whisperx/asr.py#L300

default_asr_options =  {
    "beam_size": 5,
    "best_of": 5,
    "patience": 1,
    "length_penalty": 1,
    "repetition_penalty": 1,
    "no_repeat_ngram_size": 0,
    "temperatures": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": False,
    "prompt_reset_on_temperature": 0.5,
    "initial_prompt": None,
    "prefix": None,
    "suppress_blank": True,
    "suppress_tokens": [-1],
    "without_timestamps": True,
    "max_initial_timestamp": 0.0,
    "word_timestamps": False,
    "prepend_punctuations": "\"'“¿([{-",
    "append_punctuations": "\"'.。,，!！?？:：”)]}、",
    "suppress_numerals": False,
    "max_new_tokens": None,
    "clip_timestamps": None,
    "hallucination_silence_threshold": None,
}

# %%
default_asr_options["initial_prompt"] = "Yeah, so, uh... we were... we were umm going there a hundred percent"

# %%
import whisperx
import types

compute_type = "float16"
batch_size = 16
model = whisperx.load_model("large-v2", DEVICE, asr_options=default_asr_options, language="en", compute_type=compute_type)
model.transcribe = types.MethodType(transcribe, model)

# %%
def clean_text(text):
    text = text + " "
    # https://github.com/m-bain/whisperX/blob/58f00339af7dcc9705ef49d97a1f40764b7cf555/whisperx/asr.py#L320C1-L321C53
    prepend_punctuations = "\"'“¿([{-"
    append_punctuations = "\"'.。,，!！?？:：”)]}、"
    text = text.replace("...", "")
    for punct in prepend_punctuations:
        text = text.replace(f" {punct}", " ")
    for punct in append_punctuations:
        text = text.replace(f"{punct} ", " ")
    return text.strip().lower()

# %%
def write_mfa(filename, audio, segment, base_path):
    seg_id = get_speaker_id(filename, segment['speaker'])
    ensure_directory(seg_id, base_path)
    filestem = Path(filename).stem
    output_base = f"{filestem}__{segment['start']}_{segment['end']}"
    f1 = int(segment['start'] * SAMPLE_RATE)
    f2 = int(segment['end'] * SAMPLE_RATE)
    audio_segment = audio[f1:f2]
    clean = clean_text(segment['text'])
    base_path_path = Path(base_path)
    text_filename = str(base_path_path / seg_id / f"{output_base}.txt")
    with open(text_filename, "w") as txtf:
        txtf.write(clean)
    wave_filename = str(base_path_path / seg_id / f"{output_base}.wav")
    write_wave(wave_filename, audio_segment)

# %%
def process_filepath(filepath: Path, mfa_dir, tsv_dir):
    filename = str(filepath)
    result = model.transcribe(audio=filename, batch_size=batch_size)
    full_audio = load_audio(filename)
    barefilename = filepath.stem
    tsv_path = Path(tsv_dir)
    if not tsv_path.is_dir():
        tsv_path.mkdir()

    tsv_file = str(tsv_path / f"{barefilename}_segments.tsv")
    with open(tsv_file, "w") as tsvf:
        tsvf.write("filename\tstart\tend\tspeaker_id\ttext\n")
        for segment in result['segments']:
            write_mfa(filename, full_audio, segment, mfa_dir)
            tsvf.write(f"{barefilename}.wav\t{segment['start']}\t{segment['end']}\t{segment['speaker']}\t{segment['text'].strip()}\n")

# %%
for wavfile in AUDIO_PATH.glob("*.wav"):
    if "timecode" in str(wavfile):
        continue
    process_filepath(wavfile, MFA_DIR, TSV_DIR)


