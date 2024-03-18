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


def main():
    args = get_args()
    if args.write_ffmpeg_script:
         with open(str(args.write_ffmpeg_script), "w"):
              pass


if __name__ == '__main__':
        main()
