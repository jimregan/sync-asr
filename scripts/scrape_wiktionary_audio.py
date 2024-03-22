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
from time import sleep
from urllib.parse import unquote
import argparse


LANGUAGE_PAGES = {
    "Hungarian": "https://en.wiktionary.org/wiki/Category:Hungarian_terms_with_audio_links",
    "Polish": "https://en.wiktionary.org/wiki/Category:Polish_terms_with_audio_links"
}


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


def get_audio_from_page(page: str, language: str):
    pieces = page.split("/")
    word = pieces[-1]

    req = requests.get(page)
    assert req.status_code == 200

    soup = BeautifulSoup(req.text)

    html_chunk = extract_language_chunk(soup, language)
    subsoup = BeautifulSoup(html_chunk)

    ipa = get_ipa(subsoup)
    audio = get_audio_links(subsoup)

    return {
        "word": unquote(word),
        "ipa": ipa,
        "audio": audio
    }


def process_word_links(links, language, sleeptime=3):
    audio_parts = []
    for link in links:
        audio_parts.append(get_audio_from_page(link, language))
        sleep(sleeptime)
    return audio_parts


def get_word_links(landing, sleeptime=3):
    links = []
    next_page = landing
    while next_page is not None:
        req = requests.get(next_page)
        soup = BeautifulSoup(req.text)
        links += get_category(soup)
        next_page = get_next_link(soup)
        sleep(sleeptime)
    return links


def get_args():
    parser = argparse.ArgumentParser(description="""
    Scrape (English) Wiktionary for audio links
    """)
    parser.add_argument("--extension",
                        type=str,
                        default="wav",
                        help="Audio file extension")
    parser.add_argument("--model",
                        type=str,
                        help="Huggingface model ID")
    return parser
