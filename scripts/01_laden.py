"""Stap 1: inschrijvingen leerplicht (telling 1 februari) downloaden en samenvoegen tot één compacte tabel.

Uitvoer: data/vl.pkl, geaggregeerd zonder adressen. De map data/ staat in .gitignore.
Gebruik: python scripts/01_laden.py [eerste_jaar] [laatste_jaar]
"""
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
URL = "https://opendata.dataplatform-onderwijs.vlaanderen.be/dataloep/inschrijvingen-leerplicht-instellingen-dataset-{y}-{n}-1feb.csv"
HS = {"111": "kleuter", "211": "lager", "311": "secundair", "312": "dbso",
      "121": "bu kleuter", "221": "bu lager", "321": "buso"}
KEEP = ["hoofdstructuur_inschrijving_code", "graad_so", "leerjaar", "onderwijsvorm", "finaliteit", "domein",
        "studierichting", "opleidingsvorm", "type_buitengewoon_onderwijs", "onderwijsnet", "soort_inrichtende_macht",
        "geslacht", "belg_nietbelg", "school_krijgt_omkadering_gok", "vestiging_provincie_naam",
        "vestiging_fusiegemeente_naam", "taal_code", "instellingsnummer", "administratieve_groep"]


def main(y0=2016, y1=2025):
    fr = []
    for y in range(y0, y1 + 1):
        f = DATA / f"ins_{y}.csv"
        if not f.exists() or f.stat().st_size == 0:
            r = requests.get(URL.format(y=y, n=y + 1), timeout=600)
            r.raise_for_status()
            f.write_bytes(r.content)
        d = pd.read_csv(f, usecols=lambda c: c in KEEP + ["aantal_inschrijvingen"], dtype=str)
        d["n"] = pd.to_numeric(d.pop("aantal_inschrijvingen"))
        d["jaar"] = y
        keys = [c for c in d.columns if c != "n"]
        g = d.groupby(keys, dropna=False, as_index=False, observed=True).n.sum()
        print(y, len(d), "->", len(g), int(g.n.sum()))
        fr.append(g)
    a = pd.concat(fr, ignore_index=True)
    a["hs"] = a.hoofdstructuur_inschrijving_code.map(HS)
    a["instellingsnummer"] = a.instellingsnummer.str.replace(r"\.0$", "", regex=True)
    for c in KEEP:
        a[c] = a[c].astype("category")
    a.to_pickle(DATA / "vl.pkl")
    print(a.groupby(["jaar", "hs"]).n.sum().unstack())


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 2016, int(a[1]) if len(a) > 1 else 2025)
