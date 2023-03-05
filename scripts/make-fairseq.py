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

ALIGNMENTS = Path("/home/joregan/chunked")
OUTDIR = Path("/home/joregan/sbtal_riksdag_subset3")
TMP = Path("/tmp")
parameters=["-ac", "1", "-acodec", "pcm_s16le", "-ar", "16000"]

tsv = open("/home/joregan/sbtal_subset3.tsv", "w")
ltr = open("/home/joregan/sbtal_subset3.ltr", "w")
all = open("/home/joregan/sbtal_subset-combined3.tsv", "w")


def clean(text):
    charset = "-:abcdefghijklmnoprstuvwxyzäåéö "
    for punct in ":?!.,-;":
        text = text.replace(f"{punct} ", " ")
    chars = []
    for char in text.lower():
        if char in charset:
            chars.append(char)
    return "".join(chars)


def process():
    limit = (60 * 60 * 100 * 1000)
    total = 0
    limit_reached = False
    for afile in ALIGNMENTS.glob("*"):
        temp_wav = ""
        if limit_reached:
            tsv.close()
            ltr.close()
            exit()
        with open(str(afile)) as alignment:
            counter = 1
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
                duration = end - start
                if duration > 10_000:
                    continue
                if total + duration > limit:
                    limit_reached = True
                total += duration
                text = clean(parts[4])
                piece_id = f"{vidid}_{counter}"
                counter += 1
                outwav = OUTDIR / f"{piece_id}.wav"
                audio[start:end].export(str(outwav), format="wav", parameters=parameters)
                tsv.write(f"{outwav}\t{duration}\n")
                ltr.write(" ".join(list(text.replace(" ", "|"))) + " |\n")
                all.write(f"{outwav}\t{duration}\t{text}\t{start}\t{end}\n")


if __name__ == "__main__":
    process()
