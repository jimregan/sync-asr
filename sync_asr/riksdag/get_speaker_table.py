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
import requests
import zipfile
import io
import csv


_URL = "http://data.riksdagen.se/dataset/person/person.csv.zip"


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

