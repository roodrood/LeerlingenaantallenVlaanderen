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

    out.update(schoolgrootte(a))
    out.update(aanbod(s))
    out["sig"] = signalen(a, s, out)

    json.dump(out, open(DATA / "verhaal.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("ok", (DATA / "verhaal.json").stat().st_size // 1024, "kB")


KLASSEN = [(0, 50, "<50"), (50, 100, "50-99"), (100, 200, "100-199"), (200, 300, "200-299"), (300, 400, "300-399"), (400, 1e9, "400+")]


def schoolgrootte(a):
    """Grootte per instellingsnummer (school) en per vestigingsplaats (instellingsnummer + intern volgnummer)."""
    x = a[a.hs.isin(["kleuter", "lager", "secundair"])].copy()
    x["niv"] = x.hs.astype(str).replace({"kleuter": "basis", "lager": "basis"})
    x["vest"] = x.instellingsnummer.astype(str) + "-" + x.intern_volgnr_vpl.astype(str)
    x["typ"] = np.where(x.bxl, "Brussel", np.where(x.gem.isin(C), "Centrumsteden", "Rest van Vlaanderen"))
    res = {}
    for niv in ["basis", "secundair"]:
        d = x[x.niv == niv]
        for key, nm in [("instellingsnummer", "inst"), ("vest", "vest")]:
            v = d.groupby(["jaar", key], observed=True).n.sum()
            v = v[v > 0]
            g = v.groupby(level=0)
            res[f"sg|{niv}|{nm}"] = {"aantal": [int(g.size()[y]) for y in Y], "med": [float(g.median()[y]) for y in Y],
                                     "lt100": [round(float((v[y] < 100).mean() * 100), 1) for y in Y],
                                     "lt50": [round(float((v[y] < 50).mean() * 100), 1) for y in Y]}
        v = d.groupby(["jaar", "typ", "vest"], observed=True).n.sum()
        v = v[v > 0]
        res[f"sg|{niv}|typ"] = {ty: {"aantal": [int(v[(y, ty)].size) for y in Y], "med": [float(v[(y, ty)].median()) for y in Y],
                                     "lt100": [round(float((v[(y, ty)] < 100).mean() * 100), 1) for y in Y]}
                                for ty in ["Brussel", "Centrumsteden", "Rest van Vlaanderen"]}
        v = d.groupby(["jaar", "vest"], observed=True).n.sum()
        v = v[v > 0]
        res[f"sg|{niv}|klassen"] = {str(y): [int(((v[y] >= lo) & (v[y] < hi)).sum()) for lo, hi, _ in KLASSEN] for y in Y}
    res["sg_klassen"] = [k for *_, k in KLASSEN]
    # nieuwe instellingsnummers basisonderwijs 2016-17 -> 2025-26: op een adres waar in 2016-17 al een school stond?
    def adr(y):
        f = DATA / f"ins_{y}.csv"
        if not f.exists():
            return None
        d = pd.read_csv(f, usecols=["hoofdstructuur_inschrijving_code", "instellingsnummer", "vestigingsplaats_adres"], dtype=str)
        d = d[d.hoofdstructuur_inschrijving_code.isin(["111", "211"])]
        return d.assign(adres=d.vestigingsplaats_adres.str.lower().str.strip())
    a0, a1 = adr(Y[0]), adr(Y[-1])
    if a0 is not None and a1 is not None:
        nieuw = set(a1.instellingsnummer) - set(a0.instellingsnummer)
        ad = set(a1[a1.instellingsnummer.isin(nieuw)].adres)
        res["sg_nieuw_basis"] = {"instellingen": len(nieuw), "adressen": len(ad), "bestaand_adres": len(ad & set(a0.adres))}
    return res


def aanbod(s):
    """Versnippering: aanbod = instelling x graad x onderwijsvorm x studierichting, 2e en 3e graad, zonder 7e jaar en OKAN."""
    s = s.copy()
    for c in ["leerjaar", "graad_so", "studierichting", "onderwijsvorm", "finaliteit", "administratieve_groep"]:
        s[c] = s[c].astype(str)
    z = s.leerjaar.str.contains("7e lj|Se-n-Se") | ((s.graad_so == "3e graad") & (s.leerjaar == "3e leerjaar"))
    s = s[~z & s.graad_so.isin(["2e graad", "3e graad"])]
    s["duaal"] = s.administratieve_groep.str.contains("DBSO$|SYN$") | s.studierichting.str.contains("duaal", case=False)
    u = s.groupby(["jaar", "graad_so", "instellingsnummer", "onderwijsvorm", "finaliteit", "studierichting", "duaal"], observed=True).n.sum()
    u = u[u > 0].reset_index()
    res = {"ab": {}, "ab_vt": {}}
    for (y, g), d in u.groupby(["jaar", "graad_so"]):
        for k, dd in [("ab", d), ("ab_vt", d[~d.duaal])]:
            r = dd.groupby(["onderwijsvorm", "studierichting"]).size()
            res[k][f"{g}|{y}"] = {"richtingen": int(len(r)), "aanbod": int(len(dd)), "lln": int(dd.n.sum()),
                                  "med": float(dd.n.median()), "lt10": round(float((dd.n < 10).mean() * 100), 1),
                                  "lt20": round(float((dd.n < 20).mean() * 100), 1),
                                  "lln_lt10": round(float(dd.n[dd.n < 10].sum() / dd.n.sum() * 100), 1),
                                  "per_school": round(len(dd) / dd.instellingsnummer.nunique(), 1),
                                  "scholen": int(dd.instellingsnummer.nunique()),
                                  "r1": int((r == 1).sum()), "r_lt5": int((r < 5).sum()),
                                  "kl": [int(((dd.n >= lo) & (dd.n < hi)).sum()) for lo, hi in [(0, 10), (10, 20), (20, 40), (40, 1e9)]]}
    d = u[u.jaar == 2025]
    d = d.assign(groep=np.where(d.duaal, "Duaal", d.finaliteit.str.replace("finaliteit", "", regex=False).str.strip()))
    res["ab_klein_2025"] = {f"{g}|{gr}": [int(len(v)), round(float((v.n < 10).mean() * 100), 1)] for (g, gr), v in d.groupby(["graad_so", "groep"])}
    r = d.groupby(["graad_so", "studierichting"]).agg(aanb=("n", "size"), med=("n", "median"), lln=("n", "sum")).reset_index()
    kl = r[(r.graad_so == "3e graad") & (r.aanb >= 20)].sort_values(["med", "aanb"], ascending=[True, False]).head(9)
    res["ab_kleinst_3g"] = [[x.studierichting, int(x.aanb), float(x.med), int(x.lln)] for x in kl.itertuples()]
    bins = [(1, 1, "1 school"), (2, 4, "2-4"), (5, 19, "5-19"), (20, 99, "20-99"), (100, 9999, "100+")]
    res["ab_aanb_2025"] = {g: [[lab, int(((v.aanb >= lo) & (v.aanb <= hi)).sum())] for lo, hi, lab in bins] for g, v in r.groupby("graad_so")}
    return res


def signalen(a, s, out):
    """Knipperlichten: 2023-24, 2024-25, 2025-26."""
    i = [Y.index(y) for y in (2023, 2024, 2025)]
    pick = lambda r: [r[k] for k in i]
    sl, gr = s.leerjaar.astype(str), s.graad_so.astype(str)
    net = out["net"]
    go = lambda niv: [round(net[f"{niv}|Gemeenschapsonderwijs"][k] / sum(v[k] for kk, v in net.items() if kk.startswith(niv + "|")) * 100, 2) for k in i]
    e3 = s[(gr == "3e graad") & (sl == "1e leerjaar")]
    f3 = e3.groupby(["jaar", "finaliteit"], observed=True).n.sum()
    arb = [round(float(f3[(y, "Arbeidsmarktfinaliteit")] / f3[y].sum() * 100), 1) for y in (2023, 2024, 2025)]
    du = s.administratieve_groep.astype(str).str.contains("DBSO$|SYN$") | s.studierichting.astype(str).str.contains("duaal", case=False)
    yrs = lambda q: [int(q.get(y, 0)) for y in (2023, 2024, 2025)]
    ba = out["type|bu lager"].get("Type BA") or out["type|bu lager"].get("Type basisaanbod")
    return {
        "kleuter": pick(out["niv"]["kleuter"]), "lager": pick(out["niv"]["lager"]), "1A": pick(out["sec_1A"]),
        "buso": pick(out["niv"]["buso"]), "buso9": pick(out["type|buso"]["Type 9"]),
        "bulager": pick(out["niv"]["bu lager"]), "bulager_ba": pick(ba),
        "nb_kleuter": pick(out["nb"]["kleuter"]), "go_sec": go("secundair"), "go_basis": go("basis"),
        "arb_3g1": arb, "duaal": yrs(s[du].groupby("jaar").n.sum()),
        "2B": yrs(s[sl == "2e leerjaar B"].groupby("jaar").n.sum()), "okan": pick(out["okan"]),
        "gz_3g": yrs(s[(gr == "3e graad") & (s.studierichting.astype(str) == "Gezondheidszorg") & (sl != "3e leerjaar")].groupby("jaar").n.sum()),
        "ww_3g": yrs(s[(gr == "3e graad") & (s.studierichting.astype(str) == "Welzijnswetenschappen") & (sl != "3e leerjaar")].groupby("jaar").n.sum()),
    }


if __name__ == "__main__":
    main()
