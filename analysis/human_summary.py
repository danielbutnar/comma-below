"""Totals of the human test (human/test.html) for the post: people vs models on task 4's word pairs.

Reads the result codes people sent back (human/results.txt, kept local: one line per person,
"<code>\t<who>\t<date>"). who is participant (someone I asked), dev (a code posted under the article),
retest (someone who saw version 1's answer screen before taking version 2) or author (my own run). Retests
and my own run are left out, because they knew what to look for. Writes only totals to
results/human_summary.json. Without human/results.txt (a fresh clone) it says so and leaves that file alone.
A code looks like SD6-WR2-RO1-ios-18px-390w-3.0x-63s: same/different right out of 12, "which is
right" out of 4, reads Romanian, device, word size, screen width, pixel ratio, seconds.

Version 1 of the page (those codes) marked the words as Romanian, and on a Romanian page fonts such as Segoe UI,
Roboto, Noto Sans and Open Sans draw the cedilla s with a comma: many people saw two identical words. Version 2
(10 Oct) marks the words as English and adds the right answers on the 6 identical and the 6 different pairs:
v2-SD7-S4D3-WR2-RO1-ios-18px-393w-3.0x-59s. The two versions are summarised separately. The top-level keys
are version 1. "v2" is version 2 from the people I asked who read Romanian, "v2_dev" the codes posted under
the article by people who read Romanian, and "v2_non_readers" everyone who doesn't, so a DEV reader who
can't read Romanian is never counted with the Romanians.

The answers of one person are not independent (the same eyes and the same screen), so every interval is a
95 % bootstrap over people: whole people are resampled, not answers.

Usage:  uv run --no-project python analysis/human_summary.py
"""

from __future__ import annotations

import json
import pathlib
import random
import re
import statistics
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODES = ROOT / "human" / "results.txt"
CODE = re.compile(r"SD(\d+)-WR(\d+)-R[O0]([01])-(\w+)-(\d+)px-(\d+)w-([\d.]+)x-(\d+)s")
CODE2 = re.compile(r"v2-SD(\d+)-S(\d+)D(\d+)-WR(\d+)-R[O0]([01])-(\w+)-(\d+)px-(\d+)w-([\d.]+)x-(\d+)s")
RESAMPLES = 10_000


def person_ci(rows: list[dict], field: str, per_person: int, seed: int = 0) -> list[int]:
    """95 % interval of the share right, resampling whole people with replacement."""
    rng = random.Random(seed)
    right = [r[field] for r in rows]
    n = len(right)
    shares = sorted(sum(rng.choices(right, k=n)) / (per_person * n) for _ in range(RESAMPLES))
    return [round(100 * shares[int(0.025 * RESAMPLES)]), round(100 * shares[int(0.975 * RESAMPLES) - 1])]


def summary(rows: list[dict], answers: dict[str, int]) -> dict:
    """Totals for one group of people; answers maps a field to how many answers each person gives in it."""
    n = len(rows)
    out = {"n": n, "reads_romanian": sum(r["ro"] for r in rows),
           "devices": {d: c for d, c in sorted(Counter(r["os"] for r in rows).items())}}
    for field, per in answers.items():
        k = sum(r[field] for r in rows)
        out.update({f"{field}_k": k, f"{field}_n": per * n, f"{field}_pct": round(100 * k / (per * n)),
                    f"{field}_ci": person_ci(rows, field, per)})
    out["median_seconds"] = statistics.median(r["secs"] for r in rows)
    return out


def parse(lines: list[str]) -> list[dict]:
    rows = []
    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        code, who = line.split("\t")[:2]
        who = who.strip()
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
    return rows


def summarise(rows: list[dict]) -> dict:
    out = {}
    people = [r for r in rows if r["who"] == "participant" and r["version"] == 1]
    author = [r for r in rows if r["who"] == "author" and r["version"] == 1]
    if people:
        out = summary(people, {"sd": 12, "wr": 4})
        out["author_sd"] = author[0]["sd"] if author else None
        out["author_wr"] = author[0]["wr"] if author else None
    v2 = [r for r in rows if r["version"] == 2 and r["who"] in ("participant", "dev")]
    groups = {"v2": [r for r in v2 if r["who"] == "participant" and r["ro"]],
              "v2_dev": [r for r in v2 if r["who"] == "dev" and r["ro"]],
              "v2_non_readers": [r for r in v2 if not r["ro"]]}
    for key, group in groups.items():
        if group:
            out[key] = summary(group, {"sd": 12, "same": 6, "diff": 6, "wr": 4})
            if key == "v2_non_readers":
                out[key]["sources"] = dict(sorted(Counter(r["who"] for r in group).items()))
    if out:
        out["ci"] = f"95 % bootstrap over people ({RESAMPLES:,} resamples)"
    left_out = Counter(f"v{r['version']} {r['who']}" for r in rows
                       if not (r["who"] == "participant" or (r["version"] == 2 and r["who"] == "dev")))
    if left_out:
        print("left out:", dict(sorted(left_out.items())))
    return out


def main():
    if not CODES.exists():
        print(f"{CODES.relative_to(ROOT)} is not here (it stays local), so results/human_summary.json is left as it is.")
        return
    out = summarise(parse(CODES.read_text(encoding="utf-8").splitlines()))
    (ROOT / "results" / "human_summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
