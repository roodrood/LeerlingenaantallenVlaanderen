# Voorlopige leerlingenaantallen (Discimus) ophalen en gebruiken

Handleiding om de voorlopige cijfers van een schooljaar (bv. 2026-27, peildatum 1 oktober) in een ander project te gebruiken.
Werkend voorbeeld: `scripts/04_voorlopig.py` (ophalen + vergelijking) en `scripts/05_voorlopig_verhaal.py` (volledige indeling).

## 1. De bron

| | |
|---|---|
| Bestand | `https://data-onderwijs.vlaanderen.be/documenten/bestanden/leerlingenaantallen_discimus_voorlopig_1.xlsx` |
| Uitgever | Onderwijs Vlaanderen (Discimus = de leerlingendatabank) |
| Inhoud | Nederlandstalig leerplichtonderwijs, alle niveaus, één schooljaar (kolom `schooljaar` = 2026 voor 2026-27) |
| Grootte | ±16 MB, ±100.000 rijen, één tabblad `data`, 56 kolommen |
| Stand | kolom `tijdstip_gegevens` (versie 1: 7 oktober 2026, 20:50) |
| Versies | het nummer `_1` in de bestandsnaam loopt op bij nieuwe versies; kijk dus na of er een `_2`, `_3` ... is |

## 2. Ophalen: de site weigert cloudservers

`data-onderwijs.vlaanderen.be` sluit de verbinding (TLS-reset) voor servers in de cloud, ook voor GitHub Actions.
Op een gewone pc werkt een rechtstreekse download wel.

Omweg: de connector `onderwijs-mcp` (Vercel, repo `roodrood/onderwijs-mcp`) heeft een route die bestanden van
`*.vlaanderen.be` in delen van 4 MB doorgeeft (Vercel-functies mogen niet meer dan ±4,5 MB teruggeven):

```
GET https://onderwijs-mcp-f326.vercel.app/api/bestand?url=<url>          -> {"grootte":..., "delen":5, ...}
GET https://onderwijs-mcp-f326.vercel.app/api/bestand?url=<url>&deel=0   -> ruwe bytes van deel 0, dan 1, 2, ...
```

De delen achter elkaar plakken geeft het originele xlsx-bestand. Enkel https-bestanden van vlaanderen.be worden doorgegeven.

```python
import requests

BRON = "https://data-onderwijs.vlaanderen.be/documenten/bestanden/leerlingenaantallen_discimus_voorlopig_1.xlsx"
VIA = "https://onderwijs-mcp-f326.vercel.app/api/bestand"

def ophalen(pad):
    try:                                   # werkt op een gewone pc
        r = requests.get(BRON, timeout=300); r.raise_for_status()
        open(pad, "wb").write(r.content)
    except requests.RequestException:      # in de cloud: via de connector
        info = requests.get(VIA, params={"url": BRON}, timeout=120).json()
        data = b"".join(requests.get(VIA, params={"url": BRON, "deel": i}, timeout=120).content
                        for i in range(info["delen"]))
        open(pad, "wb").write(data)
```

Inlezen: `pd.read_excel(pad, dtype={"nummer_hoofdstructuur": str, "nummer_instelling": str})` (openpyxl nodig).

## 3. Welke kolom: peildatum 1 oktober

Het bestand heeft één kolom per peildatum:

```
aantal_lln_op_instap_01_09   aantal_lln_op_teldag_01_10   aantal_lln_op_instap_herfst   aantal_lln_op_instap_kerst
aantal_lln_op_teldag_15_01   aantal_lln_op_teldag_01_02   aantal_lln_op_instap_krokus   aantal_lln_op_instap_paas
aantal_lln_op_instap_hemel   aantal_lln_op_teldag_15_05   aantal_lln_op_teldag_01_06   aantal_lln_op_30_06
```

**Gebruik `aantal_lln_op_teldag_01_10`.** De latere peildata zijn nog niet echt ingevuld: ze tonen de stand van het
moment van de export (op enkele vooraf ingeschreven instappers na). Bij een nieuwe versie van het bestand later in het
jaar kan je de volgende peildatum gebruiken.

## 4. Kolommen en codes

Belangrijkste kolommen: `nummer_instelling`, `naam_instelling`, `intern_volgnr_vpl` (vestigingsplaats),
`straatnaam_vpl`, `huisnr_vpl`, `postnummer_vpl`, `gemeente_vpl`, `fusiegemeente_vpl` (gemeenten na de fusies van 2025),
`provincie_vpl`, `naam_im` (inrichtende macht = schoolbestuur), `naam_net`, `nummer_hoofdstructuur`,
`naam_administratieve_groep`, `onderwijsvorm`, `type_buitengewoon`, `opleidingsvorm_buso`, `domein_so`, `finaliteit_so`,
`graad`, `leerjaar`, `studierichting`, `geslacht`.

| `nummer_hoofdstructuur` | |
|---|---|
| 111 / 121 | gewoon / buitengewoon kleuter |
| 211 / 221 | gewoon / buitengewoon lager |
| 311 | voltijds gewoon secundair |
| 312 | duaal leren in een centrum voor leren en werken (DBSO) |
| 315 | duaal leren bij Syntra |
| 321 | buitengewoon secundair (BuSO) |

- `leerjaar` is een getal: kleuter = 0, lager 1-6, secundair 1-3 binnen de graad.
- `graad` in het secundair: `1`, `2`, `3`, `OKAN`, `HBO` (HBO5 verpleegkunde), `Andere`. Het **7e leerjaar** = graad 3, leerjaar 3.
- **1A en 1B** staan niet apart in `leerjaar`: haal ze uit `naam_administratieve_groep` (begint met `1e lj A` of `1e lj B`).
- `naam_net`: `Gemeenschapsonderwijs`, `Officieel gesubsidieerd onderwijs`, `Vrij gesubsidieerd onderwijs`, `Andere` (Syntra).
- `opleidingsvorm_buso`: 1-4 (OV1-OV4). `type_buitengewoon`: `BA`, `2`, `3`, `4`, `5`, `6`, `7`, `9`.

## 5. Valkuilen bij vergelijken met de open data van 1 februari

De open data "inschrijvingen leerplicht per instelling" (telling 1 februari) is de gewone reeks. Bij een vergelijking:

1. **Ander moment in het schooljaar.** 1 oktober is geen 1 februari. Kleuters (instapdata) en OKAN (nieuwkomers) groeien
   tijdens het jaar: die zijn niet vergelijkbaar. Ook 7e jaar en HBO5 liggen in oktober hoger (afhakers later in het jaar),
   en verwijzingen naar het buitengewoon onderwijs gebeuren deels tijdens het jaar. Lager en secundair zijn bruikbaar, met voorzichtigheid.
2. **Marktaandelen zijn betrouwbaarder dan absolute verschillen**, want het seizoenseffect geldt voor alle scholen.
3. **Ziekenhuisscholen (type 5) weglaten.** Ze staan in het voorlopige bestand (± 600 BuSO, ± 355 buitengewoon lager,
   ± 180 buitengewoon kleuter in 2026-27), maar niet in de open data van 1 februari. Wie ze meetelt, ziet een groei die er niet is.
4. **Duaal leren**: in 2025-26 zat het in het voltijds secundair (administratieve groep eindigt op "DBSO" of "SYN"),
   in 2026-27 apart als hoofdstructuur 312 en 315. Tel 311 + 312 + 315 samen voor een vergelijkbaar secundair.
5. **Gemeenten**: beide bronnen gebruiken de fusiegemeenten van 2025; de namen komen overeen.
6. **Adressen**: de open data hebben `vestigingsplaats_adres` = "Gemeente, Straat nr"; in het voorlopige bestand bouw je dat
   als `fusiegemeente_vpl + ", " + straatnaam_vpl + " " + huisnr_vpl`.

## 6. Controlegetallen (versie 1, peildatum 1 oktober 2026, zonder type 5)

| | 1 okt 2026 | 1 feb 2026 (open data) |
|---|---|---|
| gewoon lager | 426.630 | 431.213 |
| lager, 1e leerjaar | 72.927 | 74.135 |
| secundair, 1e leerjaar A | 64.497 | 64.081 |
| secundair, 1e leerjaar B | 10.830 | 10.990 |
| secundair totaal (311+312+315) | 481.630 | 480.487 |
| BuSO | 26.884 | 26.442 |
| buitengewoon lager | 26.416 | 27.212 |

Komen je eigen tellingen hiermee overeen, dan lees je het bestand op dezelfde manier.
