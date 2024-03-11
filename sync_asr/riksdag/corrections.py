# Copyright (c) 2022, Jim O'Regan for Språkbanken Tal
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
_CORRECTIONS = """
byggsenktionsavgiften byggsanktionsavgiften
här herr
vvi vi
prisposbeloppet prisbasbeloppet
äste SD
äm M
se C
euavgiften EU-avgiften
för Fru
sveridemokraterna Sverigedemokraterna
ner ned
svärjiedemokraterna Sverigedemokraterna
sveriedemokraterna Sverigedemokraterna
utvecklingsbeståndet utvecklingsbiståndet
utvecklingsbestånd utvecklingsbistånd
katastrofbestånd katastrofbistånd
korruptionskrad korruptionsgrad
eustarter EU-stater
transperensie Transparency
trafiknytterhetsprov trafiknykterhetsprov
kommer komma
björnlund Björlund
allså alltså
ine inne
klasgöran Clas-Göran
karlson Carlsson
karlsson Carlsson
forsell Forssell
flygstriskrafterna flygstridskrafterna
deplessionen depressionen
riksreevisionen Riksrevisionen
essregeringar S-regeringar
meskick medskick
erikson Eriksson
gustavsson Gustafsson
omissligt omistligt
debatttiden debattiden
intepulation interpellation
intepelanten interpellanten
interpulationsdebatter interpellationsdebatter
mädskick medskick
interpulationsdebatterna interpellationsdebatterna
intepelationerna interpellationerna
huvurmnanskap huvudmannaskap
huvudmanskap huvudmannaskap
dödblindhet dövblindhet
tvdebatt tv-debatt
teckensprakstolkning teckenspråkstolkning
nobellpriset Nobelpriset
renome renommé
bolonja Bologna
de det
den det
eböcker e-böcker
tevelicensen tv-licensen
sveries Sveriges
tevavgift tv-avgift
tevilicensen tv-licensen
tevelicensen tv-licensen
färgtvn färg-tv:n
tvekanal tv-kanal
tvkanal tv-kanal
tevefyra TV4
smartfons smartphones
reklamfinanserade reklamfinansierade
tvinnehavet tv-innehavet
teveapparat tv-apparat
tvilicensen tv-licensen
tevelicensplikten tv-licensplikten
tveavgiftssystem tv-avgiftssystem
tven tv:n
esvete SVT
allmnhetens allmänhetens
teveföretagen tv-företagen
terorism terrorism
teroristorganisationers terroristorganisationers
teroristbrott terroristbrott
teroriseras terroriseras
terorister terrorister
afkanistan Afghanistan
maly Mali
male Mali
övvik Ö-vik
abebégymnasiet ABB-gymnasiet
abeflygplan A/B-flygplan
abefs ABF:s
abfs ABF:s
abies ABS
abieffkurserna ABF-kurserna
abief ABF
aczen Axén
adeärrkort ADR-kort
adeärr ADR
adiellbedömningen ADL-bedömningen
adiesselstationer ADSL-stationer
adihodepreparaten adhd-preparaten
adihodemediciner adhd-mediciner
adihodeläkemedel adhd-läkemedel
adihodedroger adhd-droger
aduptioner adoptioner
aeff AF
aelless ALS
aenddeesstrategin ANDTS-strategin
aettaffisch A1-affisch
aendete ANDT
aendeteanvändandet ANDT-användandet
aendeteessfrågorna ANDTS-frågorna
aendeteesspolitiken ANDTS-politiken
aendeteessstrategin ANDTS-strategin
aendetefrågan ANDT-frågan
aendetefrågor ANDT-frågor
aendeteområdet ANDT-området
aendetessområdet ANDTS-området
aendetesspolitiskt ANDTS-politiskt
aendetesstrategi ANDTS-strategi
aendetestrategi ANDT-strategi
aendetestrategin ANDT-strategin
rutavdraget RUT-avdraget
sahäll Sahel
akim Aqim
alkaida_relaterade al-Qaida-relaterade
libien Libyen
malie Mali
kunskapoc kunskap_och
adisabeba Addis_Abeba
eus EU:s
gihadister jihadister
peesertester PCR-tester
beesiärtest PCR-test
afganska afghanska
uesas USA:s
eukommissionens EU-kommissionens
nåonting någonting
svedavia Swedavia
någnting någonting
eunivå EU-nivå
elisabet Elisabeth
björnsdott Björnsdotter
ram Rahm
intepelationen interpellationen
vallmark Wallmark
sverijedemokraterna Sverigedemokraterna
stadskontoret Statskontoret
sjöstett Sjöstedt
sveriedemokrater sverigedemokrater
"""


def get_corrections():
    return {k: v for k, v in (l.split() for l in _CORRECTIONS.split('\n') if l != "")}
