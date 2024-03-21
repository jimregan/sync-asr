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
import requests
from bs4 import BeautifulSoup


def get_category(soup: BeautifulSoup):
    links = []
    cat = soup.find("div", {"class": "mw-category-generated"})
    for link in cat.findAll('li'):
        links.append(f"https://en.wiktionary.org{link.find('a')['href']}")
    return links


def get_next_link(soup: BeautifulSoup):
    cat = soup.find("div", {"class": "mw-category-generated"})
    for a in cat.findAll('a'):
        if a.text.strip() == 'next page':
            return f"https://en.wiktionary.org{a['href']}"
    return None


def extract_language_chunk(soup: BeautifulSoup, needle: str):
    pieces = []
    reading = False

    body_content = soup.find('div', {"id", "mw-parser-output"})

    for child in body_content.children:
        if child.name == "h2":
            if not reading and needle in child.text:
                reading = True
            if reading and not needle in child.text:
                reading = False
        else:
            if reading:
                pieces.append(child)

    return ''.join([str(x) for x in pieces])


def get_ipa(subsoup: BeautifulSoup):
    ipa = []
    for pron in subsoup.findAll("span", {"class": "IPA"}):
        ipa.append(pron.text)
    filtered = []
    if len(ipa) > 1:
        for pron in ipa:
            if pron.startswith("-"):
                continue
            else:
                filtered.append(pron)
    return filtered


def get_audio_links(subsoup: BeautifulSoup):
    audio = []
    for pron in subsoup.findAll("audio"):
        for filesrc in pron.findAll("source"):
            src = filesrc["src"]
            if src.startswith("//"):
                src = "https" + src
            if "/transcoded/" in src:
                continue
            else:
                audio.append(src)
    return audio

