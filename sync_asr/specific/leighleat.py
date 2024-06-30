# Copyright (c) 2023, 2024, Jim O'Regan
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


COUNT_DIGITS = {
    1: "a haon",
    2: "a dó",
    3: "a trí",
    4: "a ceathair",
    5: "a cúig",
    6: "a sé",
    7: "a seacht",
    8: "a hocht",
    9: "a naoi"
}


DIALECT_MU = {
    "anseo": "anso",
    "ansin": "ansan",
    "dtús": "dtúis",
    "tosú": "tosnú",
    "tosóidh": "tosnóidh",
    "atá": "athá",
    "atá tú": "athánn tú",
    "léi": "léithe",
    "arís": "aríst",
    "cloisteáil": "cloisint",
    "faoi": "fé",
    "an-suim": "an-shuim",
    "scríofa": "scríte",
}


PAGE_SPECIFIC = {
    "181": {
        "Mar 'Tháinig": "Mar a Tháinig",
        "Cabidil": "Caibidil",
        "mar Chuir": "mar a Chuir"
    },
    "190": {
        "nuair d'fhéach": "nuair a d'fhéach"
    },
    "191": {
        "le mo": "lem"
    }
}


def skip_if_colon(text):
    if ":" in text:
        return ""
    else:
      return text


def skip_art(text):
    if text.startswith("(Ealaín:"):
        return ""
    else:
        return text


def get_page_list(url: str):
    PAGE_REQ = requests.get(url)
    if PAGE_REQ.status_code != 200:
        return None

    soup = BeautifulSoup(PAGE_REQ.content, "html.parser")

    pages = set()
    for row in soup.find_all("div", {'class': 'row'}):
        for anchor in row.find_all("a"):
            if anchor["href"].startswith("/pages/"):
                pages.add(f'https://www.leighleat.com{anchor["href"]}')
    return list(pages)


def get_page(url: str, getnext: bool = False):
    PAGE_REQ = requests.get(url)
    if PAGE_REQ.status_code != 200:
        return None
    output = {}
    output["url"] = url

    soup = BeautifulSoup(PAGE_REQ.content, "html.parser")

    audio_url = ""
    audio = soup.find("audio", {"id": "audio"})
    if audio:
        audio_source = audio.find("source")
        if audio_source:
            if audio_source["src"].startswith("http"):
                audio_url = audio_source["src"]
            elif audio_source["src"].startswith("/"):
                audio_url = f'https://www.leighleat.com{audio_source["src"]}'

    text_pieces = []
    content = soup.find("div", {"class": "story-page-content"})
    selector = "h1, p"
    next_selector = "a.next-btn"
    if not content:
        content = soup.find("div", {"class": "inner-container"})
        selector = "h1.page-title, div.text > p"
    if not content:
        content = soup.find("div", {"class": "mobile-page-text"})
        selector = "h2, p"
    if not content:
        content = soup.find("div", {"class": "g-hidden-lg-down"})
        selector = "div.page-text > h1, div.page-text > p"
    if content:
        for text in content.select(selector):
            if text.text.strip() != "":
                text_pieces.append(text.text.strip())
    
    if getnext:
        next_button = soup.select_one(next_selector)
        output["next"] = f'https://www.leighleat.com{next_button["href"]}'

    output["audio"] = audio_url
    output["text"] = text_pieces

    return output


