# Leerlingen in Vlaanderen

Scrollverhaal over de leerlingenaantallen in het Nederlandstalig leerplichtonderwijs, schooljaren 2016-17 tot 2025-26,
op basis van **open data** (Onderwijs Vlaanderen, Federaal Planbureau/Statbel, Informatie Vlaanderen).

**Het verhaal:** `docs/index.html` (dubbelklik om te openen; werkt zonder internet, op de lettertypes na).

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

## Bijwerken na een nieuwe telling (1 februari)

```bash
pip install -r requirements.txt
python scripts/01_laden.py 2016 2026     # downloadt de open data naar data/ en voegt samen
python scripts/02_cijfers.py             # rekent alle cijfers -> data/verhaal.json
python scripts/03_verhaal.py             # bouwt docs/index.html
```

Stap 2 verwacht in `data/`: `gem.json` en `arr.json` (grenzen, zie hieronder) en `pop.xlsx`
(kopie van `bronnen/bevolking_arrondissement_FPB_Statbel.xlsx`).

Grenzen ophalen (Informatie Vlaanderen, VRBG 2025):

```bash
curl -o data/gem.json "https://geo.api.vlaanderen.be/VRBG2025/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=VRBG2025:RefgemG100&outputFormat=application/json&srsName=EPSG:4326"
curl -o data/arr.json "https://geo.api.vlaanderen.be/VRBG2025/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=VRBG2025:RefarrG100&outputFormat=application/json&srsName=EPSG:4326"
```

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
