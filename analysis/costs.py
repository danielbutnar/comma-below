"""Sum tokens and cost per task and model from downloaded run files.

Usage:  uv run --no-project python analysis/costs.py
"""

from __future__ import annotations

import json
import pathlib
from collections import defaultdict

RAW = pathlib.Path(__file__).resolve().parent.parent / "results" / "raw"


def requests(obj):
    """Yield every per-request metrics dict in a run file."""
    if isinstance(obj, dict):
        for conv in obj.get("conversations", []) or []:
            for req in conv.get("requests", []) or []:
                if "metrics" in req:
                    yield req["metrics"]
        for sub in obj.get("subruns", []) or []:
            yield from requests(sub)


def main():
    totals = defaultdict(lambda: defaultdict(float))
    for f in RAW.glob("*/*/*/*/*.run.json"):
        task, version, model = f.parts[-5], f.parts[-4], f.parts[-3]
        d = json.loads(f.read_text(encoding="utf-8"))
        t = totals[(task, model)]
        for m in requests(d):
            t["calls"] += 1
            t["in_tok"] += int(m.get("inputTokens", 0) or 0)
            t["out_tok"] += int(m.get("outputTokens", 0) or 0)
            t["usd"] += (int(m.get("inputTokensCostNanodollars", 0) or 0)
                         + int(m.get("outputTokensCostNanodollars", 0) or 0)) / 1e9
    by_model = defaultdict(float)
    for (task, model), t in sorted(totals.items()):
        by_model[model] += t["usd"]
        print(f"{task:24s} {model:32s} calls={int(t['calls']):4d} in={int(t['in_tok']):7d} "
              f"out={int(t['out_tok']):7d} ${t['usd']:.4f}")
    print()
    for model, usd in sorted(by_model.items(), key=lambda kv: -kv[1]):
        print(f"{model:32s} ${usd:.4f}")
    print(f"total ${sum(by_model.values()):.4f}")


if __name__ == "__main__":
    main()
