"""Stap 2: alle cijfers voor het verhaal berekenen -> data/verhaal.json (wordt in de HTML ingebakken).

Vereist: data/vl.pkl (stap 1), data/gem.json en data/arr.json (gemeente- en arrondissementsgrenzen,
Informatie Vlaanderen VRBG2025, gegeneraliseerd), bronnen/bevolking_arrondissement_FPB_Statbel.xlsx.
"""
import json
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
Y = list(range(2016, 2026))
C = ['Aalst', 'Antwerpen', 'Brugge', 'Genk', 'Gent', 'Hasselt', 'Kortrijk', 'Leuven', 'Mechelen', 'Oostende',
     'Roeselare', 'Sint-Niklaas', 'Turnhout']
VL_ARR = ['Antwerpen', 'Mechelen', 'Turnhout', 'Hasselt', 'Maaseik', 'Tongeren', 'Aalst', 'Dendermonde', 'Eeklo', 'Gent',
          'Oudenaarde', 'Sint-Niklaas', 'Halle-Vilvoorde', 'Leuven', 'Brugge', 'Diksmuide', 'Ieper', 'Kortrijk', 'Oostende',
          'Roeselare', 'Tielt', 'Veurne']


def reeks(s):
    return [int(s.get(y, 0)) for y in Y]


def main():
    a = pd.read_pickle(DATA / "vl.pkl")
    a["gem"] = a.vestiging_fusiegemeente_naam.astype(str)
    a["prov"] = a.vestiging_provincie_naam.astype(str)
    a["bxl"] = a.prov.str.contains("Brussel")
    out = {"Y": Y}

    # 1. niveaus
    lv = a.groupby(["hs", "jaar"], observed=True).n.sum().unstack().fillna(0)
    out["niv"] = {h: reeks(lv.loc[h]) for h in lv.index}
    s = a[a.hs == "secundair"]
    zevende = s.leerjaar.astype(str).str.contains("7e lj|Se-n-Se") | ((s.graad_so.astype(str) == "3e graad") & (s.leerjaar.astype(str) == "3e leerjaar"))
    out["sec_zonder7"] = reeks(s[~zevende].groupby("jaar").n.sum())
    out["sec_7"] = reeks(s[zevende].groupby("jaar").n.sum())
    out["sec_1A"] = reeks(s[s.leerjaar.astype(str) == "1e leerjaar A"].groupby("jaar").n.sum())
    out["sec_1B"] = reeks(s[s.leerjaar.astype(str) == "1e leerjaar B"].groupby("jaar").n.sum())

    # 2. bevolkingsvooruitzichten Vlaanderen (22 arrondissementen) en per arrondissement
    wb = openpyxl.load_workbook((DATA / "pop.xlsx" if (DATA / "pop.xlsx").exists() else ROOT / "bronnen" / "bevolking_arrondissement_FPB_Statbel.xlsx"), read_only=True, data_only=True)
    P = {}
    for arr in VL_ARR:
        rows = list(wb[arr].iter_rows(values_only=True))
        yrs = list(rows[3][1:])
        age = {int(str(r[0]).split()[0]): r[1:] for r in rows[4:116] if r[0] and "jaar" in str(r[0])}
        P[arr] = (yrs, age)
    PY = list(range(2010, 2041))

    def grp(arr, lo, hi):
        yrs, age = P[arr]
        return [sum(age[k][yrs.index(y)] for k in range(lo, hi + 1)) for y in PY]

    G = {"3-5": (3, 5), "6-11": (6, 11), "12-17": (12, 17), "0": (0, 0)}
    out["pop"] = {"yrs": PY, **{g: [sum(v) for v in zip(*[grp(arr, *r) for arr in VL_ARR])] for g, r in G.items()}}
    out["pop_arr"] = {}
    for arr in VL_ARR:
        d = {}
        for g, r in G.items():
            v = grp(arr, *r)
            d[g] = [v[PY.index(2026)], v[PY.index(2031)], v[PY.index(2036)]]  # 1 jan 2026, 2031, 2036
        out["pop_arr"][arr] = d

    # 3. gemeenten
    k = a[~a.bxl & a.hs.isin(["kleuter", "lager", "secundair"])].groupby(["gem", "hs", "jaar"], observed=True).n.sum()
    gem = {}
    for (g, h), v in k.groupby(level=[0, 1]):
        v = v.droplevel([0, 1])
        gem.setdefault(g, {})[h] = [int(v.get(2016, 0)), int(v.get(2022, 0)), int(v.get(2025, 0))]
    out["gem"] = gem
    t = a[a.hs.isin(["kleuter", "lager", "secundair", "buso"])].copy()
    t["typ"] = np.where(t.bxl, "Brussel", np.where(t.gem.isin(C), "Centrumsteden", "Rest van Vlaanderen"))
    out["typ"] = {f"{h}|{ty}": reeks(v.droplevel([0, 1])) for (h, ty), v in t.groupby(["hs", "typ", "jaar"], observed=True).n.sum().groupby(level=[0, 1])}
    out["prov"] = {f"{h}|{p}": reeks(v.droplevel([0, 1])) for (h, p), v in a[a.hs.isin(["kleuter", "lager", "secundair"]) & (a.prov != "Henegouwen")].groupby(["hs", "prov", "jaar"], observed=True).n.sum().groupby(level=[0, 1])}

    # geometrie (vereenvoudigd)
    def geo(path, key, tol):
        res = []
        for f in json.load(open(path))["features"]:
            s2 = shape(f["geometry"]).simplify(tol, preserve_topology=True)
            polys = [s2] if s2.geom_type == "Polygon" else list(s2.geoms)
            res.append({"n": f["properties"][key], "r": [[[round(x, 4), round(y, 4)] for x, y in p.exterior.coords] for p in polys if p.area > 2e-6]})
        return res
    out["G_gem"] = geo(DATA / "gem.json", "NAAM", 0.0025)
    out["G_arr"] = geo(DATA / "arr.json", "NAAM", 0.003)

    # 4. buitengewoon
    def aandeel(gewoon, bu):
        x = a[a.hs.isin(gewoon + bu)].groupby(["hs", "jaar"], observed=True).n.sum().unstack().fillna(0)
        return [round(float(x.loc[bu, y].sum() / x[y].sum() * 100), 2) for y in Y]
    out["bu_aandeel_basis"] = aandeel(["kleuter", "lager"], ["bu kleuter", "bu lager"])
    out["bu_aandeel_sec"] = aandeel(["secundair", "dbso"], ["buso"])
    for h in ["buso", "bu lager"]:
        x = a[a.hs == h].groupby(["type_buitengewoon_onderwijs", "jaar"], observed=True).n.sum().unstack().fillna(0)
        out["type|" + h] = {str(t_): reeks(x.loc[t_]) for t_ in x.index if x.loc[t_].sum() > 0}
    x = a[a.hs == "buso"].groupby(["opleidingsvorm", "jaar"], observed=True).n.sum().unstack().fillna(0)
    out["ov"] = {str(o): reeks(x.loc[o]) for o in x.index}
    x = a[(a.hs == "buso") & (a.jaar == 2025)].groupby(["opleidingsvorm", "type_buitengewoon_onderwijs"], observed=True).n.sum()
    out["ov_type_2025"] = {f"{o}|{t_}": int(v) for (o, t_), v in x.items() if v > 0}
    x = a[a.hs.isin(["bu lager", "buso", "lager", "secundair"]) & (a.jaar == 2025)].groupby(["hs", "geslacht"], observed=True).n.sum()
    out["jongens_2025"] = {h: round(float(x[(h, "Mannelijk")] / x[h].sum() * 100), 1) for h in ["bu lager", "buso", "lager", "secundair"]}

    # 5. secundair: finaliteit, oude vormen, OKAN
    f = s[(s.jaar == 2025)].groupby("finaliteit", observed=True).n.sum()
    out["fin_2025"] = {str(k_): int(v) for k_, v in f.items() if v > 0}
    o = s[(s.jaar == 2016)].groupby("onderwijsvorm", observed=True).n.sum()
    out["vorm_2016"] = {str(k_): int(v) for k_, v in o.items() if v > 0}
    out["okan"] = reeks(s[s.onderwijsvorm.astype(str).str.contains("okan")].groupby("jaar").n.sum())

    # 6. nationaliteit
    x = a[a.hs.isin(["kleuter", "lager", "secundair", "bu lager", "buso"])].groupby(["hs", "belg_nietbelg", "jaar"], observed=True).n.sum()
    out["nb"] = {h: [round(float(x.get((h, "niet-Belg", y), 0) / x.xs(h, level=0).xs(y, level=1).sum() * 100), 1) for y in Y]
                 for h in ["kleuter", "lager", "secundair", "bu lager", "buso"]}
    x = t[t.jaar == 2025].groupby(["typ", "belg_nietbelg"], observed=True).n.sum()
    out["nb_typ_2025"] = {ty: round(float(x[(ty, "niet-Belg")] / x[ty].sum() * 100), 1) for ty in ["Brussel", "Centrumsteden", "Rest van Vlaanderen"]}

    # 7. netten
    x = a[a.hs.isin(["kleuter", "lager", "secundair"])].copy()
    x["net"] = x.soort_inrichtende_macht.astype(str).replace({"Provincie": "Provincie/VGC", "VGC": "Provincie/VGC"})
    x["niv"] = x.hs.astype(str).replace({"kleuter": "basis", "lager": "basis"})
    x = x.groupby(["niv", "net", "jaar"], observed=True).n.sum()
    out["net"] = {f"{n}|{m}": reeks(v.droplevel([0, 1])) for (n, m), v in x.groupby(level=[0, 1])}

    json.dump(out, open(DATA / "verhaal.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("ok", (DATA / "verhaal.json").stat().st_size // 1024, "kB")


if __name__ == "__main__":
    main()
