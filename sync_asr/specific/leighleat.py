

import requests
from bs4 import BeautifulSoup


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


