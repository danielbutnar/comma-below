"""How much of the Romanian web still uses cedilla letters?

Fetches the front page of each site once, decodes HTML entities, and counts
comma-below (ș ț) versus cedilla (ş ţ) letters in the visible-ish text.
Writes analysis/web_census.csv.

Usage:  uv run --no-project python analysis/web_census.py
"""

from __future__ import annotations

import csv
import html
import pathlib
import re
import unicodedata
import urllib.request

SITES = [
    # national news
    "https://www.digi24.ro", "https://www.hotnews.ro", "https://adevarul.ro", "https://www.libertatea.ro",
    "https://www.g4media.ro", "https://www.gandul.ro", "https://stirileprotv.ro", "https://www.mediafax.ro",
    "https://www.agerpres.ro", "https://www.zf.ro", "https://www.economica.net", "https://www.profit.ro",
    "https://www.antena3.ro", "https://observatornews.ro", "https://www.romaniatv.net", "https://www.b1tv.ro",
    "https://www.capital.ro", "https://www.republica.ro", "https://www.edupedu.ro", "https://www.europalibera.org",
    # regional (Brașov, Iași, Cluj, Timișoara)
    "https://www.monitorulexpres.ro", "https://www.bizbrasov.ro", "https://www.newsbv.ro", "https://www.bzi.ro",
    "https://www.ziaruldeiasi.ro", "https://www.monitorulcj.ro", "https://www.tion.ro", "https://www.opiniatimisoarei.ro",
    # state and public services
    "https://www.gov.ro", "https://www.bnr.ro", "https://www.brasovcity.ro", "https://www.cfrcalatori.ro",
    # shops and classifieds
    "https://www.emag.ro", "https://www.olx.ro", "https://www.altex.ro", "https://www.elefant.ro",
    # reference
    "https://ro.wikipedia.org/wiki/Pagina_principal%C4%83",
]

COMMA = "".join(map(chr, (0x218, 0x219, 0x21A, 0x21B)))
CEDILLA = "".join(map(chr, (0x15E, 0x15F, 0x162, 0x163)))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) comma-below-census/1.0 (one request per site)"


def text_of(raw: bytes, content_type: str) -> str:
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    enc = m.group(1) if m else "utf-8"
    try:
        s = raw.decode(enc, errors="replace")
    except LookupError:
        s = raw.decode("utf-8", errors="replace")
    s = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return unicodedata.normalize("NFC", html.unescape(s))


def main():
    out = pathlib.Path(__file__).with_name("web_census.csv")
    rows = []
    for url in SITES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ro"})
            with urllib.request.urlopen(req, timeout=25) as r:
                t = text_of(r.read(), r.headers.get("Content-Type", ""))
            comma = sum(t.count(c) for c in COMMA)
            ced = sum(t.count(c) for c in CEDILLA)
            share = ced / (comma + ced) if comma + ced else None
            flat = re.sub(r"\s+", " ", t)
            hits = [m.start() for m in re.finditer(f"[{CEDILLA}]", flat)]
            examples = " | ".join(flat[max(0, i - 20):i + 12].strip() for i in hits[: 30 : 10])
            rows.append({"url": url, "comma": comma, "cedilla": ced,
                         "cedilla_share": None if share is None else round(share, 4),
                         "examples": examples, "error": ""})
        except Exception as e:  # network errors are data too
            rows.append({"url": url, "comma": "", "cedilla": "", "cedilla_share": "", "examples": "",
                         "error": repr(e)[:120]})
        print(rows[-1])
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    ok = [r for r in rows if r["cedilla_share"] not in ("", None)]
    mixed = [r for r in ok if r["cedilla"]]
    print(f"\n{len(ok)} sites measured, {len(mixed)} contain cedilla letters")


if __name__ == "__main__":
    main()
