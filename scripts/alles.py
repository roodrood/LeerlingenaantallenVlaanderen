"""Alles in één keer: data ophalen, cijfers rekenen, verhaal bouwen.

Gebruik (vanuit de map van de repository):
    pip install -r requirements.txt
    python scripts/alles.py              # schooljaren 2016-17 t/m 2025-26
    python scripts/alles.py 2016 2026    # na een nieuwe telling: laatste jaar = 2026 (schooljaar 2026-27)

Resultaat: docs/index.html. Ruwe en tussentijdse data komen in data/ (staat in .gitignore).
Bestanden die al in data/ staan, worden niet opnieuw gedownload. Verwijder ze om ze te vernieuwen.
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WFS = ("https://geo.api.vlaanderen.be/VRBG2025/wfs?service=WFS&version=2.0.0&request=GetFeature"
       "&typeNames=VRBG2025:{laag}&outputFormat=application/json&srsName=EPSG:4326")
GRENZEN = {"gem.json": "RefgemG100", "arr.json": "RefarrG100"}


def stap(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grenzen():
    for bestand, laag in GRENZEN.items():
        f = DATA / bestand
        if f.exists() and f.stat().st_size > 0:
            continue
        print("grenzen ophalen:", laag)
        r = requests.get(WFS.format(laag=laag), timeout=300)
        r.raise_for_status()
        f.write_bytes(r.content)
    pop = DATA / "pop.xlsx"
    if not pop.exists():
        shutil.copy(ROOT / "bronnen" / "bevolking_arrondissement_FPB_Statbel.xlsx", pop)


def main(y0=2016, y1=2025):
    DATA.mkdir(exist_ok=True)
    print("== 1/4 inschrijvingen ophalen en samenvoegen")
    stap("01_laden").main(y0, y1)
    print("== 2/4 grenzen en bevolking")
    grenzen()
    print("== DKO ophalen (optioneel)")
    try:
        stap("06_dko_laden").main(2018, y1)
    except Exception as e:  # zonder DKO-data bouwt het verhaal gewoon zonder hoofdstuk 10
        print("DKO overgeslagen:", e)
    print("== 3/4 cijfers rekenen")
    stap("02_cijfers").main()
    print("== 4/4 verhaal bouwen")
    stap("03_verhaal").main()
    print("klaar: docs/index.html")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 2016, int(a[1]) if len(a) > 1 else 2025)
