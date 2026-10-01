"""Every number quoted in the post, computed from the downloaded runs.

Usage:  uv run --no-project --with pandas python analysis/post_stats.py > results/post_stats.txt
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
from scoring import census  # noqa: E402

EXCLUDE = {"grok-4.6", "grok-4.5-0708", "gpt-oss-120b"}


def ok_rows(df):
    df = df[~df.model.isin(EXCLUDE)]
    return df[df["error"].isna()] if "error" in df else df


def main():
    latest = ok_rows(load())
    every = ok_rows(load(all_runs=True))
    print("models:", latest.model.nunique(), sorted(latest.model.unique()))

    # ---- Echo (all runs) ----
    e = every[every.task == "echo"]
    print("\n## Echo, all runs")
    print("runs per model:", e.groupby("model").run_id.nunique().to_dict())
    print("answers:", len(e), "| clean pass %:", round(100 * e[e.variant == "clean"]["pass"].mean(), 1),
          "| cedilla pass %:", round(100 * e[e.variant == "cedilla"]["pass"].mean(), 1))
    ce = e[e.variant == "cedilla"]
    print("cedilla input pass % by kind:", (100 * ce.groupby("kind")["pass"].mean()).round(1).to_dict())
    n_words = sum(len(x) for x in ce.cedilla_words)
    n_copied = sum(len(x) for x in ce.cedilla_words_copied)
    print(f"cedilla words in answers: {n_words}, copied verbatim from the input: {n_copied} "
          f"({100 * n_copied / n_words:.1f} %)")
    novel = Counter(w for a, b in zip(ce.cedilla_words, ce.cedilla_words_copied) for w in a if w not in b)
    print("cedilla words NOT in the input (model-made):", novel.most_common(15))
    copied = Counter(w for x in ce.cedilla_words_copied for w in x)
    print("most copied cedilla words:", copied.most_common(12))
    mixed = []
    for _, r in ce.iterrows():
        for s in re.split(r"(?<=[.!?])\s+", r.response):
            c = census(s)
            if c["cedilla"] and c["comma"]:
                mixed.append((r.model, r.item_id, s.strip()))
    print("sentences mixing both letters:", len(mixed), "in", len({(m, i) for m, i, _ in mixed}), "answers")
    for m, i, s in mixed[:40]:
        print("  ", m, i, "|", s[:200])
    worst = ce.groupby("base_id")["pass"].mean().sort_values()
    print("hardest cedilla items (pass rate):", (100 * worst.head(6)).round(0).to_dict())

    # ---- Echo with a rule (task 7) vs Echo cedilla (all runs) ----
    q = latest[latest.task == "rule"]
    if len(q):
        print("\n## Echo with a rule")
        print("answers:", len(q), "| pass %:", round(100 * q["pass"].mean(), 1),
              "| by kind:", (100 * q.groupby("kind")["pass"].mean()).round(1).to_dict())
        base = ce.groupby("model")["pass"].mean()
        rule = q.groupby("model")["pass"].mean()
        both = pd.DataFrame({"echo_cedilla_mean": (100 * base).round(1), "with_rule": (100 * rule).round(1)}).dropna()
        both["delta"] = (both.with_rule - both.echo_cedilla_mean).round(1)
        print(both.sort_values("with_rule").to_string())
        nq = sum(len(x) for x in q.cedilla_words)
        print("cedilla words left with the rule:", nq)

    # ---- Fix (latest) ----
    x = latest[latest.task == "fix"]
    print("\n## Fix")
    print("pass % by level:", (100 * x.groupby("level")["pass"].mean()).round(1).to_dict())
    l1 = x[x.level.str.startswith("L1")]
    kept = l1[(l1.typo_fixed) & (~l1["pass"].astype(bool))]
    print("L1: typo fixed but letters not repaired:", len(kept), "of", len(l1), "->",
          kept.groupby("model").size().to_dict())
    print("L1 pass by model:", (100 * l1.groupby("model")["pass"].mean()).round(0).to_dict())
    print("answers with extra text (changelog etc.):", int(x.extra_text.sum()), "of", len(x),
          "| by model:", x[x.extra_text].groupby("model").size().to_dict())

    # ---- See (latest) ----
    v = latest[latest.task == "see"]
    print("\n## See")
    for note, g in v.groupby("note"):
        print(f"  {note:30s}", (100 * g.groupby('model')['pass'].mean()).round(0).to_dict())
    ident = v[v.note.str.startswith("both")]
    always_diff = ident.groupby("model")["got"].apply(lambda s: (s == "false").all())
    print("say 'different' to every identical ș/ş pair:", sorted(always_diff[always_diff].index))
    cp = v[v.kind == "codepoint"]
    print("code point accuracy:", (100 * cp.groupby("model")["pass"].mean()).round(0).to_dict())
    print("code point wrong answers:", cp[~cp["pass"].astype(bool)][["model", "answer", "got"]].values.tolist())

    # ---- Write (latest) ----
    w = latest[latest.task == "write"]
    print("\n## Write")
    print("pass % by model:", (100 * w.groupby("model")["pass"].mean()).round(1).to_dict())
    bad = w[~w["pass"].astype(bool)]
    for _, r in bad.iterrows():
        print(f"  {r.model} {r.item_id} cedilla={r.cedilla} missing={r.missing} | {r.response[:140]!r}")

    # ---- Restore (latest) ----
    r_ = latest[latest.task == "restore"]
    print("\n## Restore")
    print("pass % by model:", (100 * r_.groupby("model")["pass"].mean()).round(1).to_dict())
    for _, r in r_[~r_["pass"].astype(bool)].iterrows():
        print(f"  {r.model} {r.item_id} if_cedilla_ok={r.pass_if_cedilla_ok} | {r.response[:100]!r}")

    # ---- Code (latest) ----
    c = latest[latest.task == "code"]
    print("\n## Code")
    print("score % by model:", (100 * c.groupby("model")["score"].mean()).round(1).to_dict())
    fails = Counter(t for lst in c.failed for t in lst)
    print("failed tests (count over", len(c), "programs):", fails.most_common())
    print("full marks:", c[c.score == 1.0][["model", "item_id"]].values.tolist())


if __name__ == "__main__":
    main()
