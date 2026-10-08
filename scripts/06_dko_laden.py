"""DKO (deeltijds kunstonderwijs): academies en inschrijvingen per administratieve groep ophalen.

Bron: inschrijvingsaantallen van Onderwijs Vlaanderen (onderwijs-API-portaal), via de route /api/export van de
connector (die gebruikt de API-key; DKO-cijfers zijn er zonder link op te vragen en worden 1 dag gecachet).
Uitvoer: data/dko_instellingen.csv, data/dko.csv (data/ wordt niet gecommit).
Gebruik: python scripts/06_dko_laden.py [eerste_jaar] [laatste_jaar]
"""
import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://onderwijs-mcp-f326.vercel.app/api/export"


def get(params, pogingen=5):
    for i in range(pogingen):
        r = requests.get(API, params={"niveau": "DKO", **params}, timeout=120)
        if r.ok:
            return pd.read_csv(io.StringIO(r.text), sep=";", dtype=str) if r.text.strip() else pd.DataFrame()
        time.sleep(5 * (i + 1))
    r.raise_for_status()


def main(y0=2018, y1=2025):
    DATA.mkdir(exist_ok=True)
    inst = get({"wat": "instellingen"})
    inst.to_csv(DATA / "dko_instellingen.csv", index=False)
    nrs = sorted(inst.instellingsnummer.astype(int).unique())
    print(len(nrs), "academies")
    jaren = ",".join(str(y) for y in range(y0, y1 + 1))
    delen = []
    for i in range(0, len(nrs), 4):
        b = nrs[i:i + 4]
        d = get({"wat": "inschrijvingen", "instellingen": ",".join(map(str, b)), "schooljaren": jaren})
        delen.append(d)
        print(i + len(b), "/", len(nrs), len(d), "rijen", flush=True)
    d = pd.concat(delen, ignore_index=True)
    d.to_csv(DATA / "dko.csv", index=False)
    print(d.shape)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 2018, int(a[1]) if len(a) > 1 else 2025)
