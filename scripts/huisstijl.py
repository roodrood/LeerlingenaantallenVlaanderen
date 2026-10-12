"""Zet de huisstijl "OBI Dashboards" op de verhalen in docs/ (opnieuw draaien vervangt de vorige versie).

Zelfde script als in de repository leerlingenmarkt-ag-so (scripts/huisstijl.py), hier voor de Vlaamse verhalen.

Huisstijl: design system "OBI Dashboards" (Claude-artifact), gebaseerd op OBI_Dashboards_Kleuroefening_2026_01.
- Witte grond, vlak (geen schaduwen), één schreefloze letter (Source Sans 3), koppen 600.
- Grafieken: geen rasterlijnen, zwarte aslijn, legende met ronde stippen.
- Kleuren per niveau, zoals in de AG SO-verhalen: kleuter = obi-grafiet, lager = obi-blauw, secundair = obi-oranje,
  buitengewoon = obi-lila.
- Groei/daling: obi-groen tegenover een donkere tint van obi-oranje (tekst moet 4,5:1 halen op wit).

Wordt aangeroepen aan het einde van scripts/03_verhaal.py en scripts/05_voorlopig_verhaal.py.
"""
import re
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "docs"

# OBI-tokens (licht / donker)
O = {"surface": ("#ffffff", "#1f2324"), "ink": ("#000000", "#f2f2f2"), "muted": ("#505050", "#b4b8b9"),
     "hair": ("#dcdcdc", "#3a4042"), "groen": ("#5e807c", "#7fa29d"), "groenl": ("#aacdc8", "#aacdc8"),
     "grafiet": ("#505050", "#8c8c8c"), "grijsl": ("#dcdcdc", "#5c6366"), "oranje": ("#f18a00", "#f18a00"),
     "oranjel": ("#ffc27b", "#ffc27b"), "blauw": ("#506d85", "#7d9bb4"), "blauwl": ("#b7dde1", "#b7dde1"),
     "lila": ("#b580d1", "#b580d1"), "lilal": ("#d7b9e4", "#d7b9e4"),
     # afgeleid (geen eigen token): donkere oranje voor tekst bij daling, zachte oranje voor de eigen rij in tabellen
     "neg": ("#a35a00", "#ffb35c"), "zacht": ("#fff1df", "#3d3020"), "land": ("#f2f2f2", "#2a3031")}

VERHAAL = {"--paper": "surface", "--card": "surface", "--ink": "ink", "--ink2": "muted", "--line": "hair", "--muted": "grijsl",
           "--k": "grafiet", "--l": "blauw", "--s": "oranje", "--bu": "lila", "--acc": "oranjel", "--water": "blauwl",
           "--pos": "groen", "--neg": "neg", "--hl": "zacht"}
KLEUREN = {"index.html": VERHAAL, "voorlopig.html": VERHAAL}
FONT = '"Source Sans 3","Myriad Pro","Segoe UI",system-ui,sans-serif'
FONTVARS = ["--f-d", "--f-b", "--display", "--body", "--f-display", "--f-body"]
LINK = '<link id="obi-font" rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap">'

# Chart.js: rasterlijnen uit, zwarte assen, ronde legendestippen, huisletter
CHARTJS = """<script id="obi-chart">(function(){if(!window.Chart||window.Chart.__obi)return;var C=window.Chart;
function ink(){return getComputedStyle(document.documentElement).getPropertyValue('--obi-ink').trim()||'#000'}
function fix(cfg){var o=cfg.options=cfg.options||{},s=o.scales||{};Object.keys(s).forEach(function(k){var a=s[k];if(!a||a.type==='radialLinear'||k==='r')return;
 a.grid=Object.assign({},a.grid,{display:false,drawOnChartArea:false});a.border=Object.assign({},a.border,{display:a.display!==false,color:ink(),width:1});
 a.ticks=Object.assign({},a.ticks,{color:ink()})});
 o.plugins=o.plugins||{};var l=o.plugins.legend=o.plugins.legend||{};l.labels=Object.assign({usePointStyle:true,pointStyle:'circle',boxWidth:8,boxHeight:8},l.labels||{});
 (cfg.data&&cfg.data.datasets||[]).forEach(function(d){if(d.borderRadius==null)d.borderRadius=0});return cfg}
var P=new Proxy(C,{construct:function(t,a){t.defaults.font.family='"Source Sans 3",sans-serif';t.defaults.color=getComputedStyle(document.documentElement).getPropertyValue('--obi-muted').trim()||'#505050';if(a[1])fix(a[1]);return Reflect.construct(t,a)}});
P.__obi=true;window.Chart=P})();</script>"""


def css(kleuren):
    def blok(i):
        return ";".join(f"{v}:{O[k][i]}!important" for v, k in kleuren.items()) + ";" + \
            ";".join(f"{v}:{FONT}!important" for v in FONTVARS) + \
            f";--obi-ink:{O['ink'][i]};--obi-muted:{O['muted'][i]};--obi-hair:{O['hair'][i]}"
    return f"""<style id="obi-css">
/* Huisstijl OBI Dashboards (scripts/huisstijl.py) */
:root{{{blok(0)}}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{blok(1)}}}}}
:root[data-theme="dark"]{{{blok(1)}}}
body,button,input,select,textarea,table{{font-family:{FONT}!important}}
h1,h2,h3,h4{{font-family:{FONT}!important;font-weight:600!important;letter-spacing:0!important}}
*{{box-shadow:none!important;text-shadow:none!important}}
.grid line{{display:none}}.grid line:first-of-type{{display:inline;stroke:var(--obi-ink)!important}}
.warn,.vlnote{{border:1px solid var(--obi-hair)!important}}
.legend span::before{{border-radius:50%!important;width:10px!important;height:10px!important}}
.vl-menu{{font-family:{FONT}!important}}.vl-menu a[aria-current=page]{{border-bottom-color:{O['oranje'][0]}!important}}
</style>"""


def main():
    for f, kleuren in KLEUREN.items():
        p = D / f
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        h = re.sub(r'<style id="obi-css">.*?</style>', "", h, flags=re.S)
        h = re.sub(r'<script id="obi-chart">.*?</script>', "", h, flags=re.S)
        h = h.replace(LINK, "")
        h = h.replace("</head>", LINK + css(kleuren) + "</head>", 1)  # na de eigen stijlen, zodat de huisstijl wint
        m = re.search(r'<script[^>]+chart\.js[^>]*></script>', h, flags=re.I)
        if m:
            h = h[:m.end()] + CHARTJS + h[m.end():]
        p.write_text(h, encoding="utf-8")
        print("huisstijl:", f)


if __name__ == "__main__":
    main()
