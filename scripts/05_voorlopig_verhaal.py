"""Verhaal 'Eerste signalen 2026-27': voorlopige cijfers van 1 oktober naast de tellingen van 1 februari.

Vereist: data/vl.pkl (stap 1), data/verhaal.json (stap 2, voor de gemeentegrenzen), data/voorlopig_2026.xlsx
(wordt opgehaald door scripts/04_voorlopig.py). Uitvoer: docs/voorlopig.html.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
N = "aantal_lln_op_teldag_01_10"
C = ['Aalst', 'Antwerpen', 'Brugge', 'Genk', 'Gent', 'Hasselt', 'Kortrijk', 'Leuven', 'Mechelen', 'Oostende',
     'Roeselare', 'Sint-Niklaas', 'Turnhout']
Y = list(range(2016, 2026))
PROV = ["Antwerpen", "Limburg", "Oost-Vlaanderen", "Vlaams-Brabant", "West-Vlaanderen", "Brussels Hoofdstedelijk Gewest"]


def nieuw(d):
    """Voorlopig 2026-27 (1 oktober) -> zelfde categorieën als de oude reeks."""
    d = d.copy()
    hs = d.nummer_hoofdstructuur
    g, lj, ag = d.graad.astype(str), d.leerjaar, d.naam_administratieve_groep.fillna("")
    sec = hs.isin(["311", "312", "315"])
    d["cat"] = None
    d.loc[hs == "111", "cat"] = "kleuter"
    d.loc[hs == "211", "cat"] = "lager " + lj.astype("Int64").astype(str)
    d.loc[sec & (g == "1") & (lj == 1) & ag.str.contains("^1e lj A"), "cat"] = "1A"
    d.loc[sec & (g == "1") & (lj == 1) & ag.str.contains("^1e lj B"), "cat"] = "1B"
    d.loc[sec & (g == "1") & (lj == 2), "cat"] = "1e graad 2e lj"
    for gg in "23":
        for l in (1, 2):
            d.loc[sec & (g == gg) & (lj == l), "cat"] = f"{gg}e graad {l}e lj"
    d.loc[sec & (g == "3") & (lj == 3), "cat"] = "7e lj"
    d.loc[sec & (g == "OKAN"), "cat"] = "OKAN"
    d.loc[sec & (g == "HBO"), "cat"] = "HBO5"
    d.loc[sec & d.cat.isna(), "cat"] = "sec ander"
    d.loc[hs == "121", "cat"] = "bu kleuter"
    d.loc[hs == "221", "cat"] = "bu lager"
    d.loc[hs == "321", "cat"] = "buso"
    # Type 5 (ziekenhuisscholen) staat niet in de open data van 1 februari: weglaten om appels met appels te vergelijken.
    d.loc[d.type_buitengewoon.astype(str) == "5", "cat"] = "type 5"
    d["type"] = d.type_buitengewoon.fillna("").astype(str).replace({"BA": "BA"})
    d["ov"] = d.opleidingsvorm_buso.map({1: "OV1", 2: "OV2", 3: "OV3", 4: "OV4"})
    return pd.DataFrame({"cat": d.cat, "gem": d.fusiegemeente_vpl, "prov": d.provincie_vpl, "type": d.type, "ov": d.ov, "n": d[N]})


def oud(a, jaar):
    o = a[a.jaar == jaar].copy()
    for c in ["leerjaar", "graad_so", "hs", "onderwijsvorm"]:
        o[c] = o[c].astype(str)
    lj, gr, hs = o.leerjaar, o.graad_so, o.hs
    cat = pd.Series(None, index=o.index, dtype=object)
    cat[hs == "kleuter"] = "kleuter"
    for i in range(1, 7):
        cat[(hs == "lager") & (lj == f"{i}e leerjaar")] = f"lager {i}"
    s = hs.isin(["secundair", "dbso"])
    z7 = lj.str.contains("7e lj|Se-n-Se") | ((gr == "3e graad") & (lj == "3e leerjaar"))
    cat[s] = "sec ander"
    cat[s & (lj == "1e leerjaar A")] = "1A"
    cat[s & (lj == "1e leerjaar B")] = "1B"
    cat[s & lj.isin(["2e leerjaar A", "2e leerjaar B"])] = "1e graad 2e lj"
    for gg in "23":
        for l in (1, 2):
            cat[s & (gr == f"{gg}e graad") & (lj == f"{l}e leerjaar")] = f"{gg}e graad {l}e lj"
    cat[s & z7] = "7e lj"
    cat[s & gr.str.contains("okan")] = "OKAN"
    cat[s & gr.str.contains("hbo")] = "HBO5"
    cat[hs == "bu kleuter"] = "bu kleuter"
    cat[hs == "bu lager"] = "bu lager"
    cat[hs == "buso"] = "buso"
    typ = o.type_buitengewoon_onderwijs.astype(str).str.replace("Type ", "", regex=False)
    ov = o.opleidingsvorm.map({"Sociale aanpassing": "OV1", "Soc.aanpassing en arbeidsgeschiktmaking": "OV2",
                               "Beroepsonderwijs": "OV3", "Algemeen,technisch,kunst- en beroepsond.": "OV4"})
    return pd.DataFrame({"cat": cat, "gem": o.vestiging_fusiegemeente_naam.astype(str), "prov": o.vestiging_provincie_naam.astype(str),
                         "type": typ, "ov": ov, "n": o.n})


LAGER = [f"lager {i}" for i in range(1, 7)]
SEC = ["1A", "1B", "1e graad 2e lj", "2e graad 1e lj", "2e graad 2e lj", "3e graad 1e lj", "3e graad 2e lj", "7e lj", "OKAN", "HBO5", "sec ander"]
SEC_GEWOON = [c for c in SEC if c not in ("OKAN", "HBO5", "sec ander", "7e lj")]


def main():
    v = nieuw(pd.read_excel(DATA / "voorlopig_2026.xlsx", dtype={"nummer_hoofdstructuur": str}))
    a = pd.read_pickle(DATA / "vl.pkl")
    reeks = {y: oud(a, y) for y in Y}
    f = reeks[2025]
    som = lambda df, cats: int(df[df.cat.isin(cats)].n.sum())
    out = {"Y": Y}
    groepen = {"lager": LAGER, "secundair": SEC, "sec_gewoon": SEC_GEWOON, "1A": ["1A"], "1B": ["1B"], "buso": ["buso"],
               "bu lager": ["bu lager"], "kleuter": ["kleuter"], "OKAN": ["OKAN"], "7e lj": ["7e lj"], "HBO5": ["HBO5"],
               "bu kleuter": ["bu kleuter"]}
    out["feb"] = {k: [som(reeks[y], c) for y in Y] for k, c in groepen.items()}
    out["okt"] = {k: som(v, c) for k, c in groepen.items()}
    out["sep"] = None
    out["cat"] = {c: [som(f, [c]), som(v, [c])] for c in LAGER + SEC}
    # per provincie en stadstype
    def regio(df):
        df = df.assign(typ=np.where(df.prov.str.contains("Brussel"), "Brussel", np.where(df.gem.isin(C), "Centrumsteden", "Rest van Vlaanderen")))
        r = {}
        for k, c in [("lager", LAGER), ("1A", ["1A"]), ("sec_gewoon", SEC_GEWOON), ("buso", ["buso"])]:
            x = df[df.cat.isin(c)]
            r[k] = {**{p: int(x[x.prov == p].n.sum()) for p in PROV}, **{t: int(x[x.typ == t].n.sum()) for t in ["Brussel", "Centrumsteden", "Rest van Vlaanderen"]}}
        return r
    out["regio"] = {"feb": regio(f), "okt": regio(v)}
    # gemeenten: lager
    gl = lambda df: df[df.cat.isin(LAGER)].groupby("gem").n.sum()
    g0, g1 = gl(f), gl(v)
    out["gem_lager"] = {g: [int(g0.get(g, 0)), int(g1.get(g, 0))] for g in sorted(set(g0.index) | set(g1.index))}
    g0, g1 = f[f.cat == "1A"].groupby("gem").n.sum(), v[v.cat == "1A"].groupby("gem").n.sum()
    out["gem_1A"] = {g: [int(g0.get(g, 0)), int(g1.get(g, 0))] for g in sorted(set(g0.index) | set(g1.index))}
    # buitengewoon
    for k, c in [("buso", "buso"), ("bu lager", "bu lager")]:
        t0, t1 = f[f.cat == c].groupby("type").n.sum(), v[v.cat == c].groupby("type").n.sum()
        out["type|" + k] = {t: [int(t0.get(t, 0)), int(t1.get(t, 0))] for t in ["9", "BA", "2", "3", "4", "7"]}
    o0, o1 = f[f.cat == "buso"].groupby("ov").n.sum(), v[v.cat == "buso"].groupby("ov").n.sum()
    out["ov"] = {o: [int(o0.get(o, 0)), int(o1.get(o, 0))] for o in ["OV1", "OV2", "OV3", "OV4"]}
    out["ba_lager_reeks"] = [int(reeks[y][(reeks[y].cat == "bu lager") & (reeks[y].type == "BA")].n.sum()) for y in Y]
    # Antwerpen
    A0, A1 = f[f.gem == "Antwerpen"], v[v.gem == "Antwerpen"]
    out["antwerpen"] = {k: [som(A0, c), som(A1, c)] for k, c in [("lager", LAGER), ("lager 1", ["lager 1"]), ("1A", ["1A"]), ("1B", ["1B"]), ("secundair", SEC), ("buso", ["buso"]), ("bu lager", ["bu lager"])]}
    vh = json.load(open(DATA / "verhaal.json"))
    out["G_gem"] = vh["G_gem"]
    out["pop"] = {k: vh["pop"][k] for k in ("yrs", "6-11", "12-17")}
    json.dump(out, open(DATA / "voorlopig.json", "w"), ensure_ascii=False, separators=(",", ":"))
    s = (ROOT / "verhaal" / "voorlopig_sjabloon.html").read_text(encoding="utf-8")
    (ROOT / "docs" / "voorlopig.html").write_text(s.replace("__DATA__", json.dumps(out, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
    print("docs/voorlopig.html")
    print(json.dumps({k: out[k] for k in ("okt", "cat", "regio", "type|buso", "type|bu lager", "ov", "ba_lager_reeks", "antwerpen")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
