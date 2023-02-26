from pathlib import Path
from .riksdag_api import RiksdagAPI, SpeakerElement


SPEAKERS = [
    "Jörgen Hellman",
    "Agneta Gille",
    "Amir Adan",
    "Teresa Carvalho",
    "Kerstin Nilsson",
    "Niclas Malmberg",
    "Carina Ståhl Herrstedt",
    "Vasiliki Tsouplaki",
    "Cecilie Tenfjord Toftby",
    "Ann-Britt Åsebol",
    "Karin Nilsson",
    "Ingemar Nilsson",
    "Mats Nordberg",
    "Ulrika Jörgensen",
    "Aylin Fazelian",
    "Björn Wiechel",
    "Sedat Dogru",
    "Oskar Öholm",
    "Eva Lohman",
    "Karin Granbom Ellison",
    "Åsa Karlsson",
    "Yilmaz Kerimo",
    "Aphram Melki",
    "Yasmine Bladelius",
    "Désirée Liljevall",
    "Erik Slottner",
    "Gustav Nilsson",
    "Linda Wemmert",
    "Mats Sander",
    "Arin Karapet",
    "Daniel Andersson",
    "David Josefsson",
]


def main():
    rdpath = Path("/Users/joregan/Playing/rdapi/api_output/")

    all_pairs = []
    for rdfile in rdpath.glob("*"):
        rdapi = RiksdagAPI(filename=str(rdfile))
        vidid = rdapi.get_vidid()
        if vidid is None or vidid == "":
            continue
        has_split_speaker = False
        for speaker in rdapi.get_speaker_elements():
            if speaker.speaker_name in SPEAKERS:
                has_split_speaker = True
        if not has_split_speaker:
            print(vidid)


if __name__ == '__main__':
    main()
