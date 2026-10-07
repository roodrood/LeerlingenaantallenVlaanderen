"""Stap 3: verhaal/sjabloon.html + data/verhaal.json -> docs/index.html (zelfstandige pagina)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    s = (ROOT / "verhaal" / "sjabloon.html").read_text(encoding="utf-8")
    d = (ROOT / "data" / "verhaal.json").read_text(encoding="utf-8")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(s.replace("__DATA__", d), encoding="utf-8")
    print("docs/index.html", len(s) + len(d) - 8, "bytes")


if __name__ == "__main__":
    main()
