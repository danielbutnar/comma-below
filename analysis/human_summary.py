"""Totals of the human test (human/test.html) for the post: people vs models on task 4's word pairs.

Reads the result codes people sent back (human/results.txt, kept local: one line per person,
"<code>\t<who>\t<date>"; who = participant, or author for my own run, which is left out because I
knew what to look for). Writes only totals to results/human_summary.json.
A code looks like SD6-WR2-RO1-ios-18px-390w-3.0x-63s: same/different right out of 12, "which is
right" out of 4, reads Romanian, device, word size, screen width, pixel ratio, seconds.

Version 1 of the page (those codes) marked the words as Romanian, and on a Romanian page fonts such as Segoe UI,
Roboto, Noto Sans and Open Sans draw the cedilla s with a comma: many people saw two identical words. Version 2
(10 Oct) marks the words as English and adds the right answers on the 6 identical and the 6 different pairs:
v2-SD7-S4D3-WR2-RO1-ios-18px-393w-3.0x-59s. The two versions are summarised separately ("v2" below).

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
CODE2 = re.compile(r"v2-SD(\d+)-S(\d+)D(\d+)-WR(\d+)-R[O0]([01])-(\w+)-(\d+)px-(\d+)w-([\d.]+)x-(\d+)s")


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
        m2 = CODE2.fullmatch(code.strip())
        if m2:
            sd, same, diff, wr, ro, os_, size, width, dpr, secs = m2.groups()
            assert int(same) + int(diff) == int(sd), f"S + D != SD in {code}"
            rows.append(dict(version=2, who=who, sd=int(sd), same=int(same), diff=int(diff), wr=int(wr), ro=ro == "1",
                             os=os_, size=int(size), width=int(width), secs=int(secs)))
            continue
        m = CODE.fullmatch(code.strip())
        assert m, f"unreadable code: {code}"
        sd, wr, ro, os_, size, width, dpr, secs = m.groups()
        rows.append(dict(version=1, who=who, sd=int(sd), wr=int(wr), ro=ro == "1", os=os_, size=int(size),
                         width=int(width), secs=int(secs)))
    people = [r for r in rows if r["who"] == "participant" and r["version"] == 1]
    author = [r for r in rows if r["who"] == "author" and r["version"] == 1]
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
    v2 = [r for r in rows if r["who"] == "participant" and r["version"] == 2]
    if v2:
        n2 = len(v2)
        k = {f: sum(r[f] for r in v2) for f in ("sd", "same", "diff", "wr")}
        out["v2"] = {
            "n": n2, "reads_romanian": sum(r["ro"] for r in v2),
            "devices": {d: sum(r["os"] == d for r in v2) for d in sorted({r["os"] for r in v2})},
            "sd_k": k["sd"], "sd_n": 12 * n2, "sd_pct": round(100 * k["sd"] / (12 * n2)),
            "sd_ci": [round(x) for x in wilson(k["sd"], 12 * n2)],
            "same_k": k["same"], "same_n": 6 * n2, "same_pct": round(100 * k["same"] / (6 * n2)),
            "diff_k": k["diff"], "diff_n": 6 * n2, "diff_pct": round(100 * k["diff"] / (6 * n2)),
            "diff_ci": [round(x) for x in wilson(k["diff"], 6 * n2)],
            "wr_k": k["wr"], "wr_n": 4 * n2, "wr_pct": round(100 * k["wr"] / (4 * n2)),
            "median_seconds": statistics.median(r["secs"] for r in v2),
        }
    (ROOT / "results" / "human_summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
