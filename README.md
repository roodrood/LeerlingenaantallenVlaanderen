# Leerlingen in Vlaanderen

Scrollverhaal over de leerlingenaantallen in het Nederlandstalig leerplichtonderwijs, schooljaren 2016-17 tot 2025-26,
op basis van **open data** (Onderwijs Vlaanderen, Federaal Planbureau/Statbel, Informatie Vlaanderen).

**Het verhaal:** `docs/index.html` (dubbelklik om te openen; werkt zonder internet, op de lettertypes na).

## Tweede verhaal: Eerste signalen 2026-27

`docs/voorlopig.html`: voorlopige cijfers van 1 oktober 2026 (Discimus) naast de telling van 1 februari 2026.
Bouwen: `python scripts/04_voorlopig.py` (haalt het bestand op) en `python scripts/05_voorlopig_verhaal.py`.
Let op: 1 oktober en 1 februari zijn andere momenten in het schooljaar (kleuters en OKAN niet vergelijkbaar).
Handleiding om de voorlopige cijfers in een ander project te gebruiken: `docs/voorlopige-cijfers.md`.

## Hoofdstukken

1. De golf rolt door de school: kleuter krimpt, lager piekte in 2019, secundair piekt nu
2. Krimp per gemeente, centrumsteden tegenover de rest, vooruitzichten per arrondissement
3. Het buitengewoon onderwijs groeit, ondanks het M-decreet (type 9, OV3 en OV4)
4. Het secundair verandert van vorm: finaliteiten, B-stroom, OKAN, 7e jaar
5. Leerlingen zonder Belgische nationaliteit
6. Netten: het GO wint terrein
7. Schoolgrootte: minder vestigingsplaatsen, meer schoolnummers
8. Versnippering van het aanbod in het secundair (kleine studierichtingen, richtingen per school, aantal aanbieders)
9. De laatste twee jaar: acht signalen (2023-24 tot 2025-26)
10. Deeltijds kunstonderwijs: groei door volwassenen en beeldende kunst (2018-19 tot 2025-26; `scripts/06_dko_laden.py`)

## Alles opnieuw draaien

```bash
pip install -r requirements.txt
python scripts/alles.py
```

Dat ene commando doet alles: de inschrijvingen 2016-17 t/m 2025-26 downloaden (ongeveer 1 GB in `data/`), de gemeente- en
arrondissementsgrenzen ophalen bij Informatie Vlaanderen, alle cijfers rekenen en `docs/index.html` bouwen. Wat al in `data/`
staat, wordt niet opnieuw gedownload. Duur: enkele minuten, vooral de download.

De stappen apart, als je er maar één wilt herhalen:

```bash
python scripts/01_laden.py 2016 2025     # open data -> data/vl.pkl
python scripts/02_cijfers.py             # alle cijfers -> data/verhaal.json
python scripts/03_verhaal.py             # sjabloon + cijfers -> docs/index.html
```

Na een nieuwe telling (1 februari): `python scripts/alles.py 2016 2026`, en pas in `scripts/02_cijfers.py` de jaren aan
(`Y`, en de vaste jaartallen in de hoofdstukken over aanbod en signalen).

**Let op bij een update:** de teksten in `verhaal/sjabloon.html` bevatten cijfers en conclusies. Lees ze na elke update na
tegen de nieuwe `data/verhaal.json`; een conclusie die vandaag klopt, kan volgend jaar niet meer kloppen.

## Afspraken

- "Vlaanderen" = Nederlandstalig leerplichtonderwijs in Vlaanderen en Brussel. Gemeenten volgens de indeling van 2025.
- Secundair "zonder 7e jaar" laat het oude 7e jaar, Se-n-Se en het nieuwe 7e leerjaar weg, om de hervorming van 2025-26 niet als daling te lezen.
- Buitengewoon onderwijs: type 1 en 8 werden in 2015-2018 vervangen door het basisaanbod (BA); type 9 bestaat sinds 2015.
- Nationaliteit is niet hetzelfde als herkomst of thuistaal.
- Schoolgrootte: school = instellingsnummer, vestigingsplaats = instellingsnummer + intern volgnummer.
- Aanbod: aanbieding = studierichting in een school (2e of 3e graad, beide leerjaren samen); klein = minder dan 10 leerlingen.
- De map `data/` staat in `.gitignore`: ruwe data worden nooit gecommit.
