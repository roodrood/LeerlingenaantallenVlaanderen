"""Voorlopige cijfers (Discimus, peildatum 1 oktober) naast de laatste telling van 1 februari.

De site data-onderwijs.vlaanderen.be weigert verbindingen van cloudservers (ook GitHub). Het bestand komt daarom
via de connector (route /api/bestand op Vercel), in delen van 4 MB. Op een gewone pc kan het ook rechtstreeks.

Gebruik: python scripts/04_voorlopig.py   (vereist data/vl.pkl uit stap 1)
Let op: 1 oktober en 1 februari zijn andere momenten in het schooljaar. Kleuters (instapdata) en OKAN groeien
tijdens het jaar, dus die zijn niet vergelijkbaar. Enkel de kolom aantal_lln_op_teldag_01_10 is ingevuld met
echte waarden; latere peildata zijn een kopie van de huidige stand.
"""
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BRON = "https://data-onderwijs.vlaanderen.be/documenten/bestanden/leerlingenaantallen_discimus_voorlopig_1.xlsx"
VIA = "https://onderwijs-mcp-f326.vercel.app/api/bestand"
N = "aantal_lln_op_teldag_01_10"


def ophalen(f):
    if f.exists():
        return
    try:
        f.write_bytes(requests.get(BRON, timeout=300).content)
    except requests.RequestException:
        info = requests.get(VIA, params={"url": BRON}, timeout=120).json()
        f.write_bytes(b"".join(requests.get(VIA, params={"url": BRON, "deel": i}, timeout=120).content for i in range(info["delen"])))


def main():
    f = DATA / "voorlopig_2026.xlsx"
    ophalen(f)
    d = pd.read_excel(f, dtype={"nummer_hoofdstructuur": str})
    d["ag"] = d.naam_administratieve_groep.fillna("")
    a = pd.read_pickle(DATA / "vl.pkl")
    o = a[a.jaar == a.jaar.max()].copy()
    for c in ["leerjaar", "graad_so", "hs"]:
        o[c] = o[c].astype(str)
    H = lambda *h: d[d.nummer_hoofdstructuur.isin(h)]
    S, os_ = H("311", "312", "315"), o[o.hs == "secundair"]
    g, lj = S.graad.astype(str), S.leerjaar
    z7 = os_.leerjaar.str.contains("7e lj|Se-n-Se") | ((os_.graad_so == "3e graad") & (os_.leerjaar == "3e leerjaar"))
    rijen = [
        ("lager", H("211")[N].sum(), o[o.hs == "lager"].n.sum()),
        ("lager 1e leerjaar", H("211").query("leerjaar == 1")[N].sum(), o[(o.hs == "lager") & (o.leerjaar == "1e leerjaar")].n.sum()),
        ("secundair 1e leerjaar A", S[(g == "1") & (lj == 1) & S.ag.str.contains("^1e lj A")][N].sum(), os_[os_.leerjaar == "1e leerjaar A"].n.sum()),
        ("secundair 1e leerjaar B", S[(g == "1") & (lj == 1) & S.ag.str.contains("^1e lj B")][N].sum(), os_[os_.leerjaar == "1e leerjaar B"].n.sum()),
        ("secundair 7e leerjaar", S[(g == "3") & (lj == 3)][N].sum(), os_[z7].n.sum()),
        ("secundair totaal", S[N].sum(), os_.n.sum()),
        ("BuSO", H("321")[N].sum(), o[o.hs == "buso"].n.sum()),
        ("buitengewoon lager", H("221")[N].sum(), o[o.hs == "bu lager"].n.sum()),
    ]
    t = pd.DataFrame(rijen, columns=["", "1 okt (voorlopig)", "1 feb (vorig schooljaar)"]).set_index("")
    t["verschil"] = t.iloc[:, 0] - t.iloc[:, 1]
    t["%"] = (t.verschil / t.iloc[:, 1] * 100).round(1)
    print(t.to_string())


if __name__ == "__main__":
    main()
