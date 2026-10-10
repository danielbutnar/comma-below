"""Totals of the human test (human/test.html) for the post: people vs models on task 4's word pairs.

Reads the result codes people sent back (human/results.txt, kept local: one line per person,
"<code>\t<who>\t<date>"; who = participant, or author for my own run, which is left out because I
knew what to look for). Writes only totals to results/human_summary.json.
A code looks like SD6-WR2-RO1-ios-18px-390w-3.0x-63s: same/different right out of 12, "which is
right" out of 4, reads Romanian, device, word size, screen width, pixel ratio, seconds.

Usage:  uv run --no-project python analysis/human_summary.py
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODE = re.compile(r"SD(\d+)-WR(\d+)-R[O0]([01])-(\w+)-(\d+)px-(\d+)w-([\d.]+)x-(\d+)s")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (100 * (c - h) / d, 100 * (c + h) / d)


def main():
    rows = []
    for line in (ROOT / "human" / "results.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        code, who = line.split("\t")[:2]
        m = CODE.fullmatch(code.strip())
        assert m, f"unreadable code: {code}"
        sd, wr, ro, os_, size, width, dpr, secs = m.groups()
        rows.append(dict(who=who, sd=int(sd), wr=int(wr), ro=ro == "1", os=os_, size=int(size), width=int(width),
                         secs=int(secs)))
    people = [r for r in rows if r["who"] == "participant"]
    author = [r for r in rows if r["who"] == "author"]
    n = len(people)
    sd_k, wr_k = sum(r["sd"] for r in people), sum(r["wr"] for r in people)
    out = {
        "n": n, "reads_romanian": sum(r["ro"] for r in people),
        "devices": {d: sum(r["os"] == d for r in people) for d in sorted({r["os"] for r in people})},
        "sd_k": sd_k, "sd_n": 12 * n, "sd_pct": round(100 * sd_k / (12 * n)), "sd_ci": [round(x) for x in wilson(sd_k, 12 * n)],
        "wr_k": wr_k, "wr_n": 4 * n, "wr_pct": round(100 * wr_k / (4 * n)), "wr_ci": [round(x) for x in wilson(wr_k, 4 * n)],
        "median_seconds": statistics.median(r["secs"] for r in people),
        "author_sd": author[0]["sd"] if author else None, "author_wr": author[0]["wr"] if author else None,
    }
    (ROOT / "results" / "human_summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
