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
import argparse
from pathlib import Path
try:
    from pydub import AudioSegment
except:
    print("Error: pydub required")
    print("Hint: pip install pydub")
    exit(1)


def get_args():
    parser = argparse.ArgumentParser(description="""
    Extract audio from Riksdag video to match sentence segments
    """)
    parser.add_argument("input_dir",
                        type=Path,
                        help="Directory containing ctmedit files.")
    parser.add_argument("output_dir",
                        type=Path,
                        help="Directory to write audio + text")
    parser.add_argument("--wav_dir",
                        type=Path,
                        default=Path("/tmp"),
                        help="Directory for pre-converted wav files")
    parser.add_argument("video_dir",
                        type=Path,
                        default=Path("/sbtal/riksdag-video/"),
                        help="Directory containing video files.")
    parser.add_argument("--write-ctm",
                        action="store_true",
                        help="Also write CTM files")
    # This exists because I've sometimes had problems with pydub not converting wav files
    parser.add_argument("--write-ffmpeg-script",
                        type=Path,
                        help="Write a script to have ffmpeg process the audio")
    args = parser.parse_args()
    return args


def get_video_id(ctmedit_file):
    with open(ctmedit_file) as f:
        for line in f:
            line = line.strip()
            if line:
                return line.split()[0]
    return None


def write_ffmpeg_script(script_path, input_dir, video_dir, wav_dir):
    seen = set()
    lines = ["#!/bin/bash\n"]
    for ctmedit_file in sorted(input_dir.iterdir()):
        vidid = get_video_id(ctmedit_file)
        if vidid is None or vidid in seen:
            continue
        seen.add(vidid)
        src = video_dir / f"{vidid}_480p.mp4"
        dst = wav_dir / f"{vidid}.wav"
        lines.append(f"ffmpeg -i {src} -acodec pcm_s16le -ac 1 -ar 16000 {dst}\n")
    with open(script_path, "w") as f:
        f.writelines(lines)
    script_path.chmod(0o755)


def main():
    args = get_args()
    if args.write_ffmpeg_script:
        write_ffmpeg_script(args.write_ffmpeg_script, args.input_dir, args.video_dir, args.wav_dir)


if __name__ == '__main__':
        main()
