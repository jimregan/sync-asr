# coding=utf-8
# Copyright 2021 The TensorFlow Datasets Authors and the HuggingFace Datasets Authors.
# Copyright (c) 2023 Jim O'Regan for Språkbanken Tal
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

# Lint as: python3
"""Datasets loader to create the Riksdag data"""
# This script is full of local paths; sorry about that
import os
from pathlib import Path
from pydub import AudioSegment
import numpy as np

import datasets
from datasets.tasks import AutomaticSpeechRecognition
from datasets.features import Audio

ALIGNMENTS = Path("/home/joregan/sbtal_riksdag_asr/alignments")
TMP = Path("/tmp")
parameters=["-ac", "1", "-acodec", "pcm_s16le", "-ar", "16000"]


class RDDataset(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("1.1.0")
    BUILDER_CONFIGS = [
        datasets.BuilderConfig(name="speech", version=VERSION, description="Data for speech recognition"),
    ]

    def _info(self):
        features = datasets.Features(
            {
                "id": datasets.Value("string"),
                "audio": datasets.Audio(sampling_rate=16_000),
                "raw": datasets.Value("string"),
                "text": datasets.Value("string"),
                "false_starts": datasets.Value("string"),
                "false_starts_lc": datasets.Value("string"),
            }
        )

        return datasets.DatasetInfo(
            description="Riksdag speech data test set",
            features=features,
            supervised_keys=None,
            task_templates=[
                AutomaticSpeechRecognition(audio_column="audio", transcription_column="text")
            ],
        )

    def _split_generators(self, dl_manager):
       return [
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={
                    "split": "test",
                },
            ),
        ]

    def _generate_examples(self, split):
        limit = (60 * 60 * 100 * 1000)
        total = 0
        limit_reached = False
        for afile in ALIGNMENTS.glob("*"):
            temp_wav = ""
            if limit_reached:
                continue
            with open(str(afile)) as alignment:
                for line in alignment.readlines():
                    if line.startswith("FILE"):
                        continue
                    parts = line.strip().split("\t")
                    if parts[3] == "MISALIGNED":
                        continue
                    vidid = parts[0]
                    temp_wav = f"/tmp/{vidid}.wav"
                    if Path(temp_wav).exists():
                        audio = AudioSegment.from_wav(temp_wav)
                    else:
                        video_file = Path("/sbtal/riksdag-video") / f"{parts[0]}_480p.mp4"
                        if video_file.exists():
                            vid_as = AudioSegment.from_file(str(video_file), "mp4")
                            vid_as.export(temp_wav, format="wav", parameters=parameters)
                            audio = AudioSegment.from_wav(temp_wav)
                        else:
                            continue
                    print(parts)
                    start = int(float(parts[1]) * 1000)
                    end = int(float(parts[2]) * 1000)
                    if (end - start) > 10_000:
                        continue
                    if total + (end - start) > limit:
                        limit_reached = True
                    total += (end - start)
                    text = parts[4]
                    piece_id = f"{vidid}_{start}_{end}"
                    yield piece_id, {
                        "id": vidid,
                        "audio": {
                            "array": np.array(audio[start:end].get_array_of_samples()),
                            "sampling_rate": 16_000
                        },
                        "text": text
                    }
