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
import json

def convert_google_asr_file_to_textgrid_times(filename, output_words=True):
    segments = []
    words = []
    last_end = 0.0

    with open(filename) as inf:
        data = json.load(inf)
    if "results" not in data:
        raise ValueError("no 'results' list, this is maybe not from Google ASR")
    for result in data["results"]:
        if len(result["alternatives"]) != 1:
            print("More than one alternative", result["alternatives"])
        item = result["alternatives"][0]
        if not "transcript" in item:
            continue
        text = item["transcript"]
        end_time = None
        start_time = last_end
        if "words" in item:
            if "startTime" in item["words"][0]:
                start_time = item["words"][0]["startTime"]
            if "words" in item:
                if "endTime" in item["words"][-1]:
                    end_time = item["words"][-1]["endTime"]
        else:
            if "resultEndTime" in item:
                end_time = item["resultEndTime"]
        if not end_time:
            print("Still no end time?", item)
            continue
        if end_time.endswith("s"):
            end_time = end_time[:-1]
        end_time = float(end_time)
        segments.append((last_end, end_time, text))
        last_end = end_time

        if output_words and "words" in item:
            for word in item["words"]:
                start = word["startTime"]
                if start[-1] == "s":
                    start = float(start[:-1])
                start = float(start)
                end = word["endTime"]
                if end[-1] == "s":
                    end = end[:-1]
                end = float(end)
                if start == end:
                    end += 0.01
                word_text = word["word"]
                words.append((start, end, word_text))

    return segments, words
