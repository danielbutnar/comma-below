"""Turn downloaded Kaggle run outputs into tables for the write-up.

Reads results/raw/<task>/<version>/<model>/<run_id>/<task>__<model>.jsonl,
keeps the newest version and run per task and model, and writes:
  results/items.csv      one row per model x item (all tasks)
  results/summary.csv    one row per model, all headline metrics
  results/summary.md     the same as a Markdown table
Usage:  uv run --no-project --with pandas python analysis/analyze.py
"""

from __future__ import annotations

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
OUT = ROOT / "results"


def load(all_runs: bool = False) -> pd.DataFrame:
    """Rows from the newest task version; the newest run per model, or every run."""
    files: dict[tuple[str, str], list[tuple[int, int, pathlib.Path]]] = {}
    for f in RAW.glob("romanian-comma-below-*/*/*/*/*.jsonl"):
        task, version, model, run_id = f.parts[-5], f.parts[-4], f.parts[-3], f.parts[-2]
        rank = (int(version) if version.isdigit() else 0, int(run_id) if run_id.isdigit() else 0)
        files.setdefault((task, model), []).append((*rank, f))
    rows = []
    for (task, model), found in files.items():
        newest_version = max(v for v, _, _ in found)
        in_version = sorted(x for x in found if x[0] == newest_version)
        for version, run_id, f in (in_version if all_runs else in_version[-1:]):
            for line in f.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                r.update(task=task.rsplit("-", 1)[-1], model=model, version=version, run_id=run_id)
                rows.append(r)
    return pd.DataFrame(rows)


def echo_runs(df_all: pd.DataFrame) -> pd.DataFrame:
    """Echo pass rate per model and run, for clean and cedilla inputs."""
    e = df_all[(df_all.task == "echo") & df_all["error"].isna()] if "error" in df_all else df_all[df_all.task == "echo"]
    g = e.groupby(["model", "run_id", "variant"])["pass"].agg(["mean", "count"]).reset_index()
    wide = g.pivot_table(index=["model", "run_id"], columns="variant", values=["mean", "count"])
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    return wide.reset_index()


def pct(x) -> float:
    return round(100 * float(x), 3) if pd.notna(x) else float("nan")


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for model, m in df.groupby("model"):
        s: dict[str, object] = {"model": model}
        errs = m[m.get("error").notna()] if "error" in m else m.iloc[0:0]
        s["errors"] = len(errs)
        m = m[m["error"].isna()] if "error" in m else m

        w = m[m.task == "write"]
        if len(w):
            s["write"] = pct(w["pass"].mean())
            s["write_knows"] = pct(w["knows_spelling"].mean())
            s["write_cedilla_items"] = int((w["cedilla"] > 0).sum())

        e = m[m.task == "echo"]
        if len(e):
            s["echo_clean"] = pct(e[e.variant == "clean"]["pass"].mean())
            s["echo"] = pct(e[e.variant == "cedilla"]["pass"].mean())
            ce = e[e.variant == "cedilla"]
            letters = ce["comma"].sum() + ce["cedilla"].sum()
            s["echo_cedilla_letter_share"] = pct(ce["cedilla"].sum() / letters) if letters else float("nan")
            for kind, g in ce.groupby("kind"):
                s[f"echo_{kind}"] = pct(g["pass"].mean())
            if "cedilla_words" in ce:
                n_ced = sum(len(x or []) for x in ce["cedilla_words"])
                n_cop = sum(len(x or []) for x in ce["cedilla_words_copied"])
                s["echo_cedilla_words"] = n_ced
                s["echo_cedilla_words_copied_pct"] = pct(n_cop / n_ced) if n_ced else float("nan")

        q = m[m.task == "rule"]
        if len(q):
            s["echo_rule"] = pct(q["pass"].mean())
            for kind, g in q.groupby("kind"):
                s[f"echo_rule_{kind}"] = pct(g["pass"].mean())

        x = m[m.task == "fix"]
        if len(x):
            s["fix"] = pct(x["pass"].mean())
            for level, g in x.groupby("level"):
                s[f"fix_{level.split('_')[0]}"] = pct(g["pass"].mean())
            l1 = x[x.level.str.startswith("L1")]
            s["fix_L1_typo_fixed"] = pct(l1["typo_fixed"].mean())
            s["fix_L1_typo_fixed_but_cedilla_kept"] = int(((l1["typo_fixed"]) & (l1["cedilla"] > 0)).sum())

        v = m[m.task == "see"]
        if len(v):
            s["see"] = pct(v["pass"].mean())
            s["see_same_comma_vs_cedilla"] = pct(v[(v.kind == "same") & (v.note == "comma vs cedilla")]["pass"].mean())
            s["see_same_identical"] = pct(v[(v.kind == "same") & v.note.str.startswith("both")]["pass"].mean())
            s["see_controls"] = pct(v[v.note.str.startswith("control")]["pass"].mean())
            s["see_detect"] = pct(v[v.kind == "detect"]["pass"].mean())
            s["see_codepoint"] = pct(v[v.kind == "codepoint"]["pass"].mean())

        r = m[m.task == "restore"]
        if len(r):
            s["restore"] = pct(r["pass"].mean())
            s["restore_if_cedilla_ok"] = pct(r["pass_if_cedilla_ok"].mean())
            s["restore_word_acc"] = pct(r["word_accuracy"].mean())

        c = m[m.task == "code"]
        if len(c):
            s["code"] = pct(c["score"].mean())
            failed = sorted({t for lst in c["failed"] for t in (lst or [])})
            s["code_failed_tests"] = ", ".join(failed)
        out.append(s)
    cols = ["model", "write", "echo", "fix", "see", "restore", "code"]
    res = pd.DataFrame(out)
    present = [c for c in cols if c in res]
    rest = [c for c in res.columns if c not in present]
    return res[present + rest].sort_values("model")


def main():
    df = load()
    if df.empty:
        print("no results downloaded yet")
        return
    df.drop(columns=[c for c in ("code",) if c in df and df[c].dtype == object], errors="ignore")
    df.to_csv(OUT / "items.csv", index=False, encoding="utf-8", lineterminator="\n")
    summary = summarize(df)
    runs = echo_runs(load(all_runs=True))
    runs.to_csv(OUT / "echo_runs.csv", index=False, encoding="utf-8", lineterminator="\n")
    full = runs[runs["count_cedilla"] >= 20]  # runs where nearly every cedilla item completed
    agg = full.groupby("model")["mean_cedilla"].agg(["mean", "min", "max", "count"]).reset_index()
    agg.columns = ["model", "echo_mean", "echo_min", "echo_max", "echo_runs"]
    for c in ("echo_mean", "echo_min", "echo_max"):
        agg[c] = (100 * agg[c]).round(3)
    summary = summary.merge(agg, on="model", how="left")
    summary.to_csv(OUT / "summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "summary.md").write_text(summary.to_markdown(index=False), encoding="utf-8", newline="\n")
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
