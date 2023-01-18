# Copyright (c) 2023, Jim O'Regan for Språkbanken Tal
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
from typing import List
import requests
import zipfile
import io
import csv
import re
from datetime import datetime


_URL = "http://data.riksdagen.se/dataset/person/person.csv.zip"


_EQUATE_IDS = {
    "0844105199517": "768d9073-e49c-4866-ab4f-00e30340670b",
    "0168348837024": "0102278739624",
}
_EQUATE_IDS.update({v: k for k, v in _EQUATE_IDS.items()})


def _get_and_extract_csv_text():
    req = requests.get(_URL)
    assert req.status_code == 200, "Error downloading zip file"
    bytes = io.BytesIO(req.content)
    zip = zipfile.ZipFile(bytes)
    assert zip.namelist() == ['person.csv'], f"Zip file does not contain person.csv: {zip.namelist()}"
    csv_file = zip.read('person.csv')
    csv_text = csv_file.decode("utf-8")
    if csv_text.startswith('\ufeff'):
        return csv_text[1:]
    else:
        return csv_text


def _get_csv_data(csv_text):
    FIELDS = [
        "Förnamn", "Efternamn", "Iort", "Parti", "Id", "Kön", "Född", 
        "Valkrets", "Status", "Webbadress", "Epostadress", "Telefonnummer",
        "Titel", "Uppdragstyp", "Uppdragsorgan", "Uppdragsroll",
        "Uppdragsrollstatus", "From", "Tom"
    ]
    sio = io.StringIO(csv_text)
    reader = csv.reader(sio)
    header = next(reader, None)
    assert header == FIELDS
    return [dict(zip(FIELDS, item)) for item in reader]


class RiksdagPerson():
    def __init__(self, data):
        self.terms = []
        self.setup(data)

    def setup(self, data):
        self.id = data["Id"]
        self.gender = "F" if data["Kön"] == "kvinna" else "M"
        self.first_name = data["Förnamn"]
        self.last_name = data["Efternamn"]
        self.birth_year = data["Född"]
        self.party = data["Parti"]
        self.terms.append(RiksdagMemberPeriod(data))
    
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.party}) ({self.birth_year})"

    def get_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def get_party(self) -> str:
        if 'party_change' in self.__dict__ and self.party_change:
            parties = set([x.party for x in self.terms])
            return ", ".join(parties)
        else:
            return self.party
    
    def disambiguate(self) -> str:
        return f"{self.id} ({self.party}, {self.birth_year})"

    def check_id(self, id):
        if self.id == id:
            return True
        elif id in _EQUATE_IDS and _EQUATE_IDS[id] == self.id:
            return True
        else:
            return False

    def update(self, data):
        assert self.check_id(data["Id"]) == True, "Person IDs do not match"
        self.terms.append(RiksdagMemberPeriod(data))
        if self.party != data["Parti"]:
            self.party_change = True
    
    def get_terms(self):
        ranges = [x.year_range() for x in self.terms]
        return ", ".join(set(ranges))


class RiksdagMemberPeriod():
    def __init__(self, data) -> None:
        self.range = YearRange(data["From"], data["Tom"])
        self.title = data["Titel"]
        self.constituency = data["Valkrets"]
        self.party = data["Parti"]

    def start_date(self):
        return self.range.start_date()

    def end_date(self):
        return self.range.end_date()

    def start_year(self):
        return self.range.start_year()

    def end_year(self):
        return self.range.end_year()
    
    def year_range(self):
        return self.range.__str__()


class YearRange():
    """
    Year ranges for political terms.
    We store the full dates, just in case, but for everything
    else, we only care about the start and end years.
    Comparison operators are implemented based on this idea:
    less than looks only at start years, greater than at end
    years.
    """
    def __init__(self, from_date: str, to_date: str) -> None:
        self.from_text = from_date
        self.to_text = to_date
        self.from_date = self._parse_date(from_date)
        self.to_date = self._parse_date(to_date)

    def __str__(self) -> str:
        start = str(self.start_year())
        end = str(self.end_year())
        if start == end:
            return start
        else:
            return "-".join([start, end])
    
    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash((self.start_year(), self.end_year()))

    def __eq__(self, other: 'YearRange'):
        return (self.start_year() == other.start_year()
            and self.end_year() == other.end_year())

    def __lt__(self, other: 'YearRange'):
        return self.start_year() < other.start_year()

    def __le__(self, other: 'YearRange'):
        return self.start_year() <= other.start_year()

    def __gt__(self, other: 'YearRange'):
        return self.end_year() > other.end_year()

    def __ge__(self, other: 'YearRange'):
        return self.end_year() >= other.end_year()

    def contains(self, other: 'YearRange'):
        return (self.end_year() >= other.end_year()
            and self.start_year() <= other.start_year())

    def consecutive(self, other: 'YearRange'):
        return (self.end_year() + 1 == other.start_year()
            or self.end_year() >= other.start_year())

    def _parse_date(self, date):
        if date == "":
            return None
        if re.match(r"^\d\d\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d", date):
            out_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            out_date = datetime.strptime(date, '%Y-%m-%d')
        return out_date

    def start_date(self):
        return self.from_date

    def end_date(self):
        return self.to_date

    def start_year(self):
        date = self.start_date()
        if date is None:
            return ""
        return date.year

    def end_year(self):
        date = self.end_date()
        if date is None:
            return ""
        return date.year


def merge_year_ranges(ranges: List[YearRange]) -> List[YearRange]:
    collapsed = list(set(ranges))
    sorted(collapsed)
    print(collapsed)
    cur = collapsed[0]

    out = []
    i = 1
    for i in range(i, len(collapsed)):

        if cur.contains(collapsed[i]):
            i += 1
        elif cur > collapsed[i]:
            i += 1
        elif cur.consecutive(collapsed[i]):
            cur = YearRange(cur.from_text, collapsed[i].to_text)
        else:
            out.append(cur)
            cur = collapsed[i]
            i += 1
    out.append(cur)
    return out


def get_people():
    csv_text = _get_and_extract_csv_text()
    data = _get_csv_data(csv_text)

    people = {}
    for datum in data:
        if datum["Id"] in people:
            people[datum["Id"]].update(datum)
        else:
            if datum["Id"] in _EQUATE_IDS:
                new_key = _EQUATE_IDS[datum["Id"]]
                if new_key in people:
                    people[new_key].update(datum)
                else:
                    people[datum["Id"]] = RiksdagPerson(datum)
            else:
                people[datum["Id"]] = RiksdagPerson(datum)

    return people


def check_overlap(people):
    people_by_name = {}
    for person_id in people:
        person = people[person_id]
        if person.get_name() not in people_by_name:
            people_by_name[person.get_name()] = []
            people_by_name[person.get_name()].append(person.disambiguate())
        else:
            people_by_name[person.get_name()].append(person.disambiguate())
    
    for person in people_by_name:
        if len(people_by_name[person]) != 1:
            print(f"{person}: {' '.join(people_by_name[person])}")



_MD_HEADER = """
| Type | Segment | Gender | Year |
|------|---------|--------|------|
"""


def get_terms(people):
    for person in people.values():
        print(f"{person.get_name()}\t{person.gender}\t{person.get_party()}\t{person.birth_year}\t{person.get_terms()}")


def get_args():
    parser = argparse.ArgumentParser(description="""
    Work with the Riksdag people data
    """)
    parser.add_argument('--check-overlap', action="store_true",
        help="check where politicians have the same name, different IDs")
    parser.add_argument('--get-terms', action="store_true",
        help="output a list of term ranges by politician")
    args = parser.parse_args()

    return args


def main():
    args = get_args()
    people = get_people()

    if args.check_overlap:
        check_overlap(people)
        exit(0)

    if args.get_terms:
        get_terms(people)
        exit(0)


if __name__ == '__main__':
    main()
