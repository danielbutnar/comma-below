"""Which of the census sites with cedilla letters mark their pages as Romanian?

On a page marked Romanian (lang="ro"), fonts with a Romanian localized-forms rule (Segoe UI, Roboto, Noto Sans and
Open Sans among them) draw the cedilla ş ţ with a comma, so the wrong letter looks right to the site's own readers.
Reads analysis/web_census.csv (the 30 September census; the same 29 sites the post counts), fetches each front page
once and writes the language the page declares on its <html> tag to analysis/web_lang.new.csv; with --update it
replaces analysis/web_lang.csv, the 10 October snapshot the post quotes (a rerun sees different pages, and offline
it would write error rows, which check_claims.py refuses).

Usage:  uv run --no-project python analysis/web_lang.py [--update]
"""

from __future__ import annotations

import csv
import datetime
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) comma-below-census/1.0 (one request per site)"
HTML_LANG = re.compile(r"<html\b[^>]*?\b(?:xml:)?lang\s*=\s*[\"']?([A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*)", re.I)


def sites_with_cedilla() -> list[str]:
    """The census sites with cedilla letters in Romanian words (as check_claims counts them)."""
    out = []
    for r in csv.DictReader(open(HERE / "web_census.csv", encoding="utf-8")):
        if r["error"] or "wikipedia" in r["url"]:  # Wikipedia's only cedilla is Talysh, where it is right
            continue
        if int(float(r["cedilla"])) > 0:
            out.append(r["url"])
    return out


def main():
    rows = []
    for url in sites_with_cedilla():
        lang, error = "", ""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ro"})
            with urllib.request.urlopen(req, timeout=25) as r:
                head = r.read(200_000).decode("utf-8", errors="replace")
            m = HTML_LANG.search(head)
            lang = m.group(1) if m else "(none)"
        except Exception as e:  # network errors are data too
            error = repr(e)[:120]
        rows.append({"url": url, "html_lang": lang, "error": error})
        print(rows[-1])
    out = HERE / ("web_lang.csv" if "--update" in sys.argv else "web_lang.new.csv")
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        fh.write(f"# fetched {datetime.date.today().isoformat()}\n")
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    ok = [r for r in rows if not r["error"]]
    ro = [r for r in ok if r["html_lang"].lower().startswith("ro")]
    print(f"\n{len(rows)} sites with cedilla letters; fetched {len(ok)}; marked Romanian: {len(ro)}")


if __name__ == "__main__":
    main()
