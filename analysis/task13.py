"""Task 13 (other wrong letters): the analysis pre-registered in the task description.

Every s/t letter of the source's words is classified by how the answer writes it: kept in the
input's wrong form, comma below, cedilla, or bare (slot counts written by the task). Answers with
none of the source's s/t words are no data. Intervals are 95 % percentile bootstraps that resample
whole clusters; each contrast is bootstrapped twice, over models and over the 8 source texts, and
the wider interval is reported.

Usage:  uv run --no-project --with pandas --with numpy python analysis/task13.py [RAW_DIR|-] [OUT_DIR] > results/task13_stats.txt
"""

from __future__ import annotations

import math
import os
import pathlib
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
import analyze  # noqa: E402
import build  # noqa: E402
import models as M  # noqa: E402

RNG = np.random.default_rng(20261009)
B = 4000
KEPT = {"cedilla": "cedilla", "dot": "dot", "legacy": "legacy", "cedilla+scoped": "cedilla",
        "cedilla+rule": "cedilla"}
WRONG_INPUTS = ["cedilla", "dot", "legacy"]
FORMS = ["comma", "cedilla", "dot", "legacy", "bare", "other"]
COMMA, CEDILLA = set("șȘțȚ"), set("şŞţŢ")
DOT, LEGACY = set("ṣṢṭṬ"), set("ºªþÞ")
_KEY = str.maketrans({"ă": "a", "Ă": "A", "â": "a", "Â": "A", "î": "i", "Î": "I", "ș": "s", "Ș": "S",
                      "ț": "t", "Ț": "T", "ş": "s", "Ş": "S", "ţ": "t", "Ţ": "T", "ṣ": "s", "Ṣ": "S",
                      "ṭ": "t", "Ṭ": "T", "º": "s", "ª": "S", "þ": "t", "Þ": "T", "ã": "a", "Ã": "A"})
_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)


def key(word: str) -> str:
    return unicodedata.normalize("NFC", word).translate(_KEY).casefold()


def form_of(word: str) -> str | None:
    """The s/t form of a word, or None when it has no s/t diacritic of any kind."""
    letters = set(word)
    for name, group in (("cedilla", CEDILLA), ("dot", DOT), ("legacy", LEGACY), ("comma", COMMA)):
        if letters & group:
            return name
    return None


def text_id(item_id: str) -> str:
    """E07-dot -> E07; Q01-E07-dot -> E07 (the source text an item is built on)."""
    parts = item_id.split("-")
    return parts[1] if parts[0].startswith("Q") else parts[0]


def load_rows(raw: pathlib.Path | None) -> pd.DataFrame:
    if raw is not None:
        analyze.RAW = raw
    df = analyze.load(all_runs=True)
    if df.empty or "task" not in df:
        return df
    return prepare(df)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Task 13 rows with an answer, plus the source text, the kept-letter count and the encoding-talk flag."""
    df = df[df.task == "wrong"]
    df = df[df["error"].isna()] if "error" in df else df
    df = df[df.response.fillna("").astype(str).str.strip() != ""]
    df = df[~df.model.isin({"grok-4.6", "grok-4.5-0708"})].copy()
    df["text"] = df.item_id.map(text_id)
    df["kept"] = [r[f"sl_st_{KEPT[v]}"] for r, v in zip(df.to_dict("records"), df.variant)]
    df["talk"] = df.encoding_talk.map(lambda x: bool(x) if isinstance(x, list) else False)
    return df


def boot_ratio_diff(parts: pd.DataFrame, cluster: str, num_a: str, den_a: str, num_b: str, den_b: str):
    """Bootstrap of sum(num_a)/sum(den_a) - sum(num_b)/sum(den_b), resampling clusters."""
    g = parts.groupby(cluster)[[num_a, den_a, num_b, den_b]].sum()
    if len(g) < 2:
        return (math.nan, math.nan)
    v = g.values
    idx = RNG.integers(0, len(g), size=(B, len(g)))
    s = v[idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = s[:, 0] / s[:, 1] - s[:, 2] / s[:, 3]
    return tuple(100 * np.nanpercentile(d, [2.5, 97.5]))


def wider(a, b):
    return (min(a[0], b[0]), max(a[1], b[1]))


def paired(df: pd.DataFrame, va: str, vb: str):
    """Kept share of s/t letters, input va vs input vb, on model x prompt pairs with data in both."""
    cols = ["model", "run_id", "base_id", "text"]
    a = df[(df.variant == va) & (df.sl_st > 0)][cols + ["kept", "sl_st"]]
    b = df[(df.variant == vb) & (df.sl_st > 0)][cols + ["kept", "sl_st"]]
    m = a.merge(b, on=["model", "run_id", "base_id", "text"], suffixes=("_a", "_b"))
    if m.empty:
        return None
    share_a = 100 * m.kept_a.sum() / m.sl_st_a.sum()
    share_b = 100 * m.kept_b.sum() / m.sl_st_b.sum()
    ci = wider(boot_ratio_diff(m, "model", "kept_a", "sl_st_a", "kept_b", "sl_st_b"),
               boot_ratio_diff(m, "text", "kept_a", "sl_st_a", "kept_b", "sl_st_b"))
    per_model = (m.groupby("model").kept_a.sum() / m.groupby("model").sl_st_a.sum()
                 - m.groupby("model").kept_b.sum() / m.groupby("model").sl_st_b.sum())
    return {"a": share_a, "b": share_b, "diff": share_a - share_b, "lo": ci[0], "hi": ci[1], "pairs": len(m),
            "models": m.model.nunique(), "models_lower": int((per_model < 0).sum()),
            "models_higher": int((per_model > 0).sum())}


def slot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per input: how the source's s/t letters come back, pooled over answers with data."""
    rows = []
    for v, g in df.groupby("variant"):
        d = g[g.sl_st > 0]
        tot = d.sl_st.sum()
        row = {"input": v, "answers": len(g), "no_data": int((g.sl_st == 0).sum()), "letters": int(tot),
               "kept": 100 * d.kept.sum() / tot if tot else math.nan,
               "talk": int(g.talk.sum()), "clean_answers": 100 * g["pass"].mean()}
        for f in FORMS:
            row[f] = 100 * d[f"sl_st_{f}"].sum() / tot if tot else math.nan
        rows.append(row)
    order = ["cedilla", "dot", "legacy", "cedilla+scoped", "cedilla+rule"]
    t = pd.DataFrame(rows).set_index("input")
    return t.reindex([o for o in order if o in t.index])


def own_words(df: pd.DataFrame, variant: str) -> dict:
    """Prediction 5: in answers that copy the wrong form, do the model's own new s/t words follow it?
    'New' as in own_words.py: not in the source and not an inflection of a source word."""
    items = {r["item_id"]: r for r in build.data_wrong_letters()}
    wrong = KEPT[variant]
    groups = {"all": [0, 0, 0], "some": [0, 0, 0], "none": [0, 0, 0]}  # [answers, new words, new words wrong]
    for r in df[df.variant == variant].to_dict("records"):
        src = {key(w) for w in _WORD.findall(unicodedata.normalize("NFC", items[r["item_id"]]["gold"]))}
        tokens = [(w, form_of(w)) for w in _WORD.findall(unicodedata.normalize("NFC", r["response"]))]
        tokens = [(w, f) for w, f in tokens if f]
        source = [f for w, f in tokens if origin(key(w), src) == "source"]
        new = [f for w, f in tokens if origin(key(w), src) == "new"]
        if not source or not new:
            continue
        kept = sum(f == wrong for f in source)
        g = "all" if kept == len(source) else "some" if kept else "none"
        groups[g][0] += 1
        groups[g][1] += len(new)
        groups[g][2] += sum(f == wrong for f in new)
    return groups


def origin(k: str, src: set[str]) -> str:
    """'source', 'inflected' (a shared start of 5 letters, or every hyphen part a source word) or 'new'."""
    if k in src:
        return "source"
    if all(p in src for p in k.split("-")) or any(len(os.path.commonprefix([k, x])) >= 5 for x in src):
        return "inflected"
    return "new"


def per_model(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for m, g in df.groupby("model"):
        row = {"model": m, "name": M.name(m) if hasattr(M, "name") else m}
        for v in ["cedilla", "dot", "legacy", "cedilla+scoped", "cedilla+rule"]:
            d = g[(g.variant == v) & (g.sl_st > 0)]
            row[f"kept_{v}"] = round(100 * d.kept.sum() / d.sl_st.sum(), 1) if d.sl_st.sum() else math.nan
            row[f"clean_{v}"] = round(100 * g[g.variant == v]["pass"].mean(), 1) if (g.variant == v).any() else math.nan
        out.append(row)
    return pd.DataFrame(out).sort_values("kept_cedilla", ascending=False)


def main():
    raw = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("results")
    df = load_rows(raw)
    if df.empty:
        print("no task 13 runs yet")
        return
    print(f"Task 13: {df.model.nunique()} models, {len(df)} answers, {df.run_id.nunique()} runs\n")
    pd.set_option("display.width", 160)
    print("How the source's s/t letters come back (% of letters; answers with data):")
    print(slot_table(df).round(1).to_string(), "\n")
    print("Without answers that comment on the encoding:")
    print(slot_table(df[~df.talk]).round(1)[["letters", "kept", "comma", "cedilla", "bare"]].to_string(), "\n")

    print("Pre-registered predictions")
    p1 = paired(df, "dot", "cedilla")
    if p1:
        verdict = "held" if p1["hi"] < 0 else "not held"
        print(f"(1) dot below vs cedilla, kept share of s/t letters: {p1['a']:.1f} % vs {p1['b']:.1f} %, "
              f"difference {p1['diff']:+.1f} points (95 % CI {p1['lo']:+.1f} to {p1['hi']:+.1f}); "
              f"{p1['pairs']} pairs, {p1['models']} models ({p1['models_lower']} lower, {p1['models_higher']} higher) "
              f"-> {verdict}")
    p2 = paired(df, "legacy", "cedilla")
    if p2:
        verdict = "held" if p2["hi"] < 0 else "not held"
        print(f"(2) old mojibake vs cedilla: {p2['a']:.1f} % vs {p2['b']:.1f} %, difference {p2['diff']:+.1f} "
              f"(95 % CI {p2['lo']:+.1f} to {p2['hi']:+.1f}) -> {verdict}")
    rep = df[df.variant.isin(["dot", "legacy"]) & (df.sl_st > 0)]
    fixed = rep[[f"sl_st_{f}" for f in ("comma", "cedilla", "bare", "other")]].sum()
    if fixed.sum():
        share = 100 * fixed["sl_st_comma"] / fixed.sum()
        print(f"(3) dot-below and mojibake letters not kept: {share:.1f} % became comma below, "
              f"{100 * fixed['sl_st_cedilla'] / fixed.sum():.1f} % cedilla, {100 * fixed['sl_st_bare'] / fixed.sum():.1f} % bare "
              f"({int(fixed.sum())} letters) -> {'held' if share >= 90 else 'not held'}")
    sc, fu = df[df.variant == "cedilla+scoped"], df[df.variant == "cedilla+rule"]
    if len(sc) and len(fu):
        a, b = 100 * sc["pass"].mean(), 100 * fu["pass"].mean()
        keys = ["model", "run_id", "base_id", "text"]
        m = sc[keys + ["pass"]].merge(fu[keys + ["pass"]], on=keys, suffixes=("_s", "_f"))
        m[["pass_s", "pass_f"]] = m[["pass_s", "pass_f"]].astype(float)
        m["one_s"], m["one_f"] = 1, 1
        ci = wider(boot_ratio_diff(m, "model", "pass_s", "one_s", "pass_f", "one_f"),
                   boot_ratio_diff(m, "text", "pass_s", "one_s", "pass_f", "one_f"))
        ok = a >= 90 and b >= 90 and abs(a - b) <= 5
        print(f"(4) clean answers: scoped rule {a:.1f} %, full rule {b:.1f} %, difference {a - b:+.1f} "
              f"(95 % CI {ci[0]:+.1f} to {ci[1]:+.1f}) -> {'held' if ok else 'not held'}")
    g = own_words(df, "cedilla")
    sa = 100 * g["all"][2] / g["all"][1] if g["all"][1] else math.nan
    ss = 100 * g["some"][2] / g["some"][1] if g["some"][1] else math.nan
    verdict = "too few words" if math.isnan(sa) or math.isnan(ss) else ("held" if sa >= 80 and ss <= 30 else "not held")
    print(f"(5) own new s/t words with the cedilla: {g['all'][2]}/{g['all'][1]} = {sa:.0f} % when the answer kept "
          f"every cedilla ({g['all'][0]} answers), {g['some'][2]}/{g['some'][1]} = {ss:.0f} % when it kept some "
          f"({g['some'][0]} answers), {g['none'][2]}/{g['none'][1]} when it kept none -> {verdict}")
    for v in ("dot", "legacy"):
        g = own_words(df, v)
        print(f"    exploratory, {v}: own words in the {v} form {g['all'][2]}/{g['all'][1]} (kept all), "
              f"{g['some'][2]}/{g['some'][1]} (kept some), {g['none'][2]}/{g['none'][1]} (kept none)")
    print("\nPer model (kept share of s/t letters, %):")
    pm = per_model(df)
    print(pm.to_string(index=False))
    pm.to_csv(out_dir / "task13_models.csv", index=False)


if __name__ == "__main__":
    main()
