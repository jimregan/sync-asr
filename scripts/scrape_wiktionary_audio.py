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
from pathlib import Path


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
        "audio": audio,
        "page": page
    }


def process_word_links(links, language, sleeptime=10):
    audio_parts = []
    for link in links:
        audio_parts.append(get_audio_from_page(link, language))
        sleep(sleeptime)
    return audio_parts


def get_word_links(landing, sleeptime=10):
    links = []
    next_page = landing
    while next_page is not None:
        req = requests.get(next_page)
        soup = BeautifulSoup(req.text)
        links += get_category(soup)
        next_page = get_next_link(soup)
        sleep(sleeptime)
    return links


def proc_ipa_base(ipa_string):
    if ipa_string.startswith('[') and ipa_string.endswith(']'):
        ipa_string = ipa_string[1:-1]
    elif ipa_string.startswith('/') and ipa_string.endswith('/'):
        ipa_string = ipa_string[1:-1]
    ipa_string = ipa_string.replace("ˈ", "")
    ipa_string = ipa_string.replace("ˌ", "")
    ipa_string = ipa_string.replace(" ː", "ː").replace(" ͡ ", "͡")
    return ipa_string


def proc_ipa_hungarian(ipa_string):
    ipa_string = proc_ipa_base(ipa_string)
    expanded = " ".join(list(ipa_string))
    expanded = expanded.replace("ɱ", "m")
    expanded = expanded.replace(" u ̯",  "u̯")
    return expanded


def proc_ipa_polish(ipa_string):
    ipa_string = proc_ipa_base(ipa_string)
    expanded = " ".join(list(ipa_string))
    expanded = expanded.replace(".", "")
    return expanded


PROC_IPA = {
    "Hungarian": proc_ipa_hungarian,
    "Polish": proc_ipa_polish,
}


def process_pronunciations(audio_parts, proc_ipa):
    pronunciations = []

    for item in audio_parts:
        word = item["word"]
        for ipa in item["ipa"]:
            pronunciations.append(f"{word}\t{proc_ipa(ipa)}")
    return pronunciations


def write_items(grabber_sh: Path, outdir: Path, audio_parts):
    if not outdir.is_dir():
        outdir.mkdir()

    with open(str(grabber_sh), "w") as grab:
        for item in audio_parts:
            word = item["word"]
            i = 0
            for i in range(0, len(item["audio"])):
                num = str(i) if i != 0 else ""
                ext = item['audio'][i].split(".")[-1]
                if item['ipa'] == []:
                    comment = "# "
                else:
                    comment = ""
                grab.write(f"{comment}wget {item['audio'][i].replace('https//', 'https://')} -O /home/joregan/wiktionary_hu/{word}{num}.{ext}\n")
                grab.write(f"{comment}sleep 10\n")
                outfile = outdir / f"{word}{num}.txt"
                with open(str(outfile), "w") as of:
                    of.write(word.replace("_", " "))


def get_args():
    parser = argparse.ArgumentParser(description="""
    Scrape (English) Wiktionary for audio links
    """)
    parser.add_argument("--language",
                        type=str,
                        help="Language to scrape")
    parser.add_argument("--output",
                        type=str,
                        help="Output directory")
    parser.add_argument("--links",
                        type=Path,
                        help="Output text file containing word links from category")
    parser.add_argument("--save-json",
                        type=Path,
                        help="Output json containing results")
    parser.add_argument("--write-dict",
                        type=Path,
                        help="Output dict file containing pronunciations")
    
    return parser


def main():
    args = get_args()

    if args.language and args.language in LANGUAGE_PAGES:
        LANG = args.language
        PAGE = LANGUAGE_PAGES[LANG]
    else:
        PAGE = f"https://en.wiktionary.org/wiki/Category:{args.language}_terms_with_audio_links"
        LANG = args.language
        req = requests.get(PAGE)
        if req.status_code != 200:
            print(f"No Wiktionary pronunciation category found for {args.language}")
            exit(1)

    links = get_word_links(PAGE)

    if args.links:
        with open(str(args.links), "w") as of:
            for link in links:
                of.write(link + "\n")

    if LANG in PROC_IPA:
        proc_ipa = PROC_IPA[LANG]
    else:
        proc_ipa = lambda x: x

    audio_parts = process_word_links(links, LANG)

    if args.write_dict:
        pronunciations = process_pronunciations(audio_parts, proc_ipa)
        with open(args.write_dict, "w") as of:
            for pr in pronunciations:
                of.write(pr + "\n")

    grabber_sh = args.output / "grab.sh"
    write_items(grabber_sh, args.output, audio_parts)


if __name__ == '__main__':
        main()
