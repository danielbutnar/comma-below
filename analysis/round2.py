"""Round 2 numbers (tasks 8-12), with uncertainty, from the downloaded runs.

Intervals are 95 % percentile bootstraps that resample source items (all variants and runs of an
item move together), so items that are hard for every model do not shrink the interval. Paired
contrasts on the same items use an exact McNemar test. Version trends inside a product line use a
permutation test of the Spearman correlation between version and pass rate.

Usage:  uv run --no-project --with pandas --with numpy python analysis/round2.py > results/round2_stats.txt
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
import models as M  # noqa: E402

RNG = np.random.default_rng(20261008)
B = 4000
OUT = "results"
# Listed by Kaggle in October 2026 but every call returned 404.
NOT_SERVED = {"grok-4.6", "grok-4.5-0708"}


ROUND2 = {"echo4", "contagion", "turkish", "lookalike", "turns", "wrong"}


def ok_rows(df):
    """Rows without a harness error. In Round 2 an empty visible answer (a reasoning model that
    thought past the 8,192-token cap) is not an answer either, and is left out."""
    df = df[df["error"].isna()] if "error" in df else df
    if "response" in df and "task" in df:
        empty = df.task.isin(ROUND2) & (df.response.fillna("").astype(str).str.strip() == "")
        df = df[~empty]
    return df


def no_answer_counts(df):
    d = df[df["error"].isna()] if "error" in df else df
    empty = d.task.isin(ROUND2) & (d.response.fillna("").astype(str).str.strip() == "")
    return d[empty].groupby(["task", "model"]).size()


def boot_ci(values_by_cluster: dict, B: int = B) -> tuple[float, float]:
    keys = list(values_by_cluster)
    if not keys:
        return (math.nan, math.nan)
    arrs = [np.asarray(values_by_cluster[k], dtype=float) for k in keys]
    sums = np.array([a.sum() for a in arrs])
    lens = np.array([len(a) for a in arrs])
    idx = RNG.integers(0, len(keys), size=(B, len(keys)))
    means = sums[idx].sum(axis=1) / lens[idx].sum(axis=1)
    return tuple(100 * np.percentile(means, [2.5, 97.5]))


def rate_ci(df, cluster="base_id", col="pass"):
    groups = {k: g[col].astype(float).values for k, g in df.groupby(cluster)}
    lo, hi = boot_ci(groups)
    return 100 * df[col].astype(float).mean(), lo, hi, len(df)


def mcnemar(a: pd.Series, b: pd.Series) -> tuple[int, int, float]:
    """a, b: paired booleans (same index). Returns (a only, b only, exact two-sided p)."""
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    n10 = int(((j.a == 1) & (j.b == 0)).sum())
    n01 = int(((j.a == 0) & (j.b == 1)).sum())
    n = n10 + n01
    if n == 0:
        return n10, n01, 1.0
    k = min(n10, n01)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return n10, n01, min(1.0, 2 * p)


def paired_items(a: pd.DataFrame, b: pd.DataFrame, n_perm: int = 20000) -> tuple[float, float, int]:
    """Two models on the same prompts: mean per-prompt difference in pass rate (b - a, points) and a
    sign-flip permutation p-value over prompts (runs are averaged within a prompt first)."""
    pa = a.groupby("base_id")["pass"].mean()
    pb = b.groupby("base_id")["pass"].mean()
    d = (pb - pa).dropna().values
    if len(d) == 0:
        return math.nan, math.nan, 0
    obs = d.mean()
    signs = RNG.choice([-1.0, 1.0], size=(n_perm, len(d)))
    perm = (signs * d).mean(axis=1)
    p = float((np.abs(perm) >= abs(obs) - 1e-12).mean())
    return 100 * obs, p, len(d)


def spearman(x, y) -> float:
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    if np.std(rx) == 0 or np.std(ry) == 0:
        return math.nan
    return float(np.corrcoef(rx, ry)[0, 1])


def perm_trend(points: list[tuple[str, float, float]], n_perm: int = 20000) -> tuple[float, float]:
    """points: (line, version, pass rate). Mean within-line Spearman rho and a permutation p-value
    (versions shuffled within each line)."""
    lines = {}
    for ln, v, y in points:
        lines.setdefault(ln, []).append((v, y))
    lines = {k: v for k, v in lines.items() if len(v) >= 3}
    if not lines:
        return math.nan, math.nan

    def stat(ls):
        rs = [spearman([v for v, _ in pts], [y for _, y in pts]) for pts in ls.values()]
        rs = [r for r in rs if not math.isnan(r)]
        return float(np.mean(rs)) if rs else math.nan

    obs = stat(lines)
    count = 0
    for _ in range(n_perm):
        shuffled = {k: list(zip(RNG.permutation([v for v, _ in pts]), [y for _, y in pts])) for k, pts in lines.items()}
        s = stat(shuffled)
        if abs(s) >= abs(obs) - 1e-12:
            count += 1
    return obs, count / n_perm


def fmt(r):
    p, lo, hi, n = r
    return f"{p:5.1f} [{lo:4.1f}, {hi:5.1f}] n={n}"


_RO_ONLY = set("ăĂțȚ")
_TR_ONLY = set("ıİğĞöÖüÜçÇ")
_RO_FUNCTION = {"și", "în", "vă", "să", "sunt", "este", "pentru", "cu", "ne", "nu", "la", "de", "mai"}
_TR_FUNCTION = {"ve", "bir", "için", "bu", "da", "de", "ile", "mi", "mı", "çok", "olarak"}
_FOLD = str.maketrans("ăâîșțşţĂÂÎȘȚŞŢ", "aaiststAAISTST")
# Romanian words that turn up code-switched inside otherwise Turkish sentences
_RO_WORDS = {"și", "așa", "oraș", "orașul", "orașului", "orașe"}
# Romanian place names a reply may quote (either s letter is defensible inside a name)
_NAMES = ("brasov", "rasnov", "bunesti", "sambures", "timisoara", "iasi", "bucuresti", "sighisoara", "mures",
          "arges", "constanta", "pitesti", "cismigiu", "transfagarasan")


def _sentence_language(sentence: str, words: list) -> str:
    low = [w.casefold() for w in words]
    tr = sum(ch in _TR_ONLY for ch in sentence) + sum(w in _TR_FUNCTION for w in low)
    ro = 2 * sum(ch in _RO_ONLY for ch in sentence) + sum(w in _RO_FUNCTION for w in low)
    return "tr" if tr > ro else ("ro" if ro > tr else "?")


def turkish_reply_words(response: str, prompt: str) -> dict:
    """Classify every word with the Romanian comma ș in a reply to a Turkish guest, by the language of its
    sentence: a Turkish word spelled with ș (over-correction), a Romanian word (the reply slipped into
    Romanian), or a Romanian place name (either letter is defensible there)."""
    from scoring import words as _w
    out = {"tr_comma": [], "ro": [], "name": [], "unknown": []}
    romanian = False
    for sent in re.split(r"(?<=[.!?])\s+", response or ""):
        ws = _w(sent)
        lang = _sentence_language(sent, ws)
        romanian |= lang == "ro"
        for w in ws:
            if not set(w) & set("șȘ"):
                continue
            if w.casefold().translate(_FOLD).startswith(_NAMES):
                out["name"].append(w)
            elif w.casefold() in _RO_WORDS:
                out["ro"].append(w)
                romanian = True
            elif lang == "tr":
                out["tr_comma"].append(w)
            elif lang == "ro":
                out["ro"].append(w)
            else:
                out["unknown"].append(w)
    out["romanian_text"] = romanian
    return out


def turkish_outcomes(tr: pd.DataFrame):
    """One outcome per reply to a Turkish guest (task 10), from a word-level reading whose word
    lists main() prints for checking by hand: turkish_with_comma (a Turkish word written with ș),
    romanian (the reply slipped into Romanian), no_s (no s letter of either kind), or correct.
    Returns the rows with an `outcome` column and the word lists behind them."""
    from items import TURKISH as _TR
    prompts = dict(_TR)
    tt = tr[tr.lang == "tr"].copy()
    cls = [turkish_reply_words(r.response, prompts[r.base_id]) for r in tt.itertuples()]
    tt["tr_comma"] = [len(c["tr_comma"]) > 0 for c in cls]
    tt["romanian_text"] = [c["romanian_text"] for c in cls]
    tt["kept_s"] = tt.s_cedilla > 0

    def outcome(r):
        if r.tr_comma:
            return "turkish_with_comma"
        if r.romanian_text:
            return "romanian"
        if not r.kept_s:
            return "no_s"
        return "correct"

    tt["outcome"] = [outcome(r) for r in tt.itertuples()]
    return tt, cls


def purity(response: str) -> float:
    from scoring import census
    c = census(response)
    tot = c["comma"] + c["cedilla"]
    return c["cedilla"] / tot if tot else math.nan


def main():
    raw = load(all_runs=True)
    na = no_answer_counts(raw)
    if len(na):
        print("no visible answer, left out:", {f"{t}/{m}": int(n) for (t, m), n in na.items()})
    every = ok_rows(raw)
    every = every[~every.model.isin(NOT_SERVED)]
    r2 = every[every.task.isin(["echo4", "contagion", "turkish", "lookalike", "turns"])]
    keep = [c for c in ("task", "model", "version", "run_id", "item_id", "base_id", "set_id", "pair_id", "kind",
                        "variant", "cond", "lang", "rule", "pass", "comma", "cedilla", "st_total", "st_comma",
                        "st_cedilla", "st_ascii", "s_cedilla", "s_comma", "s_comma_in_names", "cyrillic",
                        "mojibake", "first_cedilla", "second_cedilla", "first", "response") if c in r2]
    r2[keep].to_csv(f"{OUT}/items_round2.csv", index=False)

    # ------------------------------------------------------------------ task 8
    e4 = every[every.task == "echo4"].copy()
    print("## Task 8: Echo, four inputs")
    if len(e4):
        print("models:", e4.model.nunique(), "| answers:", len(e4), "| runs per model:",
              dict(Counter(e4.groupby("model").run_id.nunique())))
        for v in ("clean", "cedilla", "ascii", "cedilla+rule"):
            print(f"  {v:13s} pooled pass % {fmt(rate_ci(e4[e4.variant == v]))}")
        for kind in ("reply", "summary", "rag"):
            k = e4[e4.kind == kind]
            print(f"  {kind:8s} " + " | ".join(f"{v} {100 * k[k.variant == v]['pass'].mean():.0f}"
                                            for v in ("clean", "cedilla", "ascii", "cedilla+rule")))
        # word level: how the source's s/t words were spelled
        for v in ("cedilla", "ascii"):
            s = e4[e4.variant == v]
            tot = s.st_total.sum()
            print(f"  {v}: source s/t words in answers {int(tot)}; kept cedilla {100 * s.st_cedilla.sum() / tot:.1f} %;"
                  f" left without diacritic {100 * s.st_ascii.sum() / tot:.1f} %; correct {100 * s.st_comma.sum() / tot:.1f} %")
        # paired contrasts on identical items (per model and run)
        key = ["model", "run_id", "base_id"]
        piv = e4.pivot_table(index=key, columns="variant", values="pass", aggfunc="first").astype(float)
        for a, b in (("ascii", "cedilla"), ("cedilla+rule", "cedilla"), ("clean", "cedilla")):
            if a in piv and b in piv:
                n10, n01, p = mcnemar(piv[a], piv[b])
                print(f"  McNemar {a} vs {b}: {a} only {n10}, {b} only {n01}, p = {p:.2g}")
        # per model table. For the Round 1 models, task 2 (clean, cedilla) and task 7 (cedilla + rule) sent the
        # very same prompts, so their runs are pooled with task 8's.
        r1 = every[every.task.isin(["echo", "rule"]) & every.model.isin(set(e4.model))]
        e4x = pd.concat([e4, r1[[c for c in e4.columns if c in r1.columns]]], ignore_index=True)
        rows = []
        for model, m in e4x.groupby("model"):
            row = {"model": model, "name": M.name(model), "lab": M.lab(model), "line": M.line(model),
                   "version": M.version(model), "open": M.open_weights(model)}
            for v in ("clean", "cedilla", "ascii", "cedilla+rule"):
                p, lo, hi, n = rate_ci(m[m.variant == v])
                row.update({f"{v}": p, f"{v}_lo": lo, f"{v}_hi": hi, f"{v}_n": n})
            fails = m[(m.variant == "cedilla") & (~m["pass"].astype(bool))]
            pur = [purity(x) for x in fails.response]
            pur = [x for x in pur if not math.isnan(x)]
            row["fails"] = len(fails)
            row["runs"] = m[m.variant == "cedilla"].groupby(["task", "run_id"]).ngroups
            row["whole_answer_share"] = 100 * np.mean([x == 1.0 for x in pur]) if pur else math.nan
            rows.append(row)
        t = pd.DataFrame(rows).sort_values("cedilla", ascending=False)
        t.to_csv(f"{OUT}/round2_echo4_models.csv", index=False)
        cols = ["name", "runs", "clean", "cedilla", "cedilla_lo", "cedilla_hi", "ascii", "cedilla+rule", "fails", "whole_answer_share"]
        print(t[cols].round(1).to_string(index=False))
        # version trends inside product lines (cedilla input)
        pts = [(r.line, r.version, r.cedilla) for r in t.itertuples()]
        rho, p = perm_trend(pts)
        print(f"  version trend (cedilla pass, within lines with >= 3 versions): mean Spearman rho {rho:.2f}, permutation p {p:.3f}")
        steps = []
        ced = e4x[e4x.variant == "cedilla"]
        for ln, g in t.groupby("line"):
            if len(g) >= 2:
                g = g.sort_values("version")
                print(f"    {ln}: " + " -> ".join(f"{n} {c:.0f}" for n, c in zip(g.name, g.cedilla)))
                ms = list(g.model)
                for a, b in zip(ms, ms[1:]):
                    diff, p, n = paired_items(ced[ced.model == a], ced[ced.model == b])
                    kind = "version" if ln in M.VERSION_LINES else "pair"
                    steps.append(dict(line=ln, kind=kind, older=M.name(a), newer=M.name(b), change=diff, p=p, prompts=n))
        if steps:
            st = pd.DataFrame(steps)
            st.to_csv(f"{OUT}/round2_version_steps.csv", index=False)
            print("  version steps and pairs (same 22 prompts; change in clean-answer points, sign-flip permutation p):")
            for r in st.itertuples():
                flag = " *" if r.p < 0.05 else ""
                print(f"    [{r.kind}] {r.older} -> {r.newer}: {r.change:+.0f} points, p = {r.p:.3f}{flag}")
        for a, b in M.REASONING_PAIRS:
            if a in set(t.model) and b in set(t.model):
                ra, rb = t.set_index("model").loc[a], t.set_index("model").loc[b]
                print(f"  reasoning on/off: {ra['name']} {ra.cedilla:.0f} vs {rb['name']} {rb.cedilla:.0f}")
        op = t.groupby("open")["cedilla"].mean()
        print("  mean cedilla pass by open weights:", op.round(1).to_dict())
        print("  mean cedilla pass by lab:", t.groupby("lab")["cedilla"].mean().round(1).to_dict())

    # ------------------------------------------------------------------ task 9
    k9 = every[every.task == "contagion"].copy()
    print("\n## Task 9: Contagion")
    if len(k9):
        print("models:", k9.model.nunique(), "| answers:", len(k9))
        for cond in ("clean-0", "clean-1", "clean-3", "cedilla-0", "cedilla-3"):
            print(f"  {cond:10s} pass % {fmt(rate_ci(k9[k9.cond == cond], cluster='set_id'))}")
        clean = k9[k9.target_variant == "clean"]
        src = Counter()
        for r in clean.itertuples():
            src["from other documents"] += len(r.from_others)
            src["new words"] += len(r.novel)
        print("  cedilla words in clean-target answers:", dict(src))
        per = k9.pivot_table(index="model", columns="cond", values="pass", aggfunc="mean") * 100
        per.index = [M.name(i) for i in per.index]
        print(per.round(0).to_string())
        per.to_csv(f"{OUT}/round2_contagion_models.csv")

    # ------------------------------------------------------------------ task 10
    tr = every[every.task == "turkish"].copy()
    print("\n## Task 10: Turkish guests")
    if len(tr):
        print("models:", tr.model.nunique(), "| answers:", len(tr))
        for lang in ("tr", "ro"):
            for rule in ("none", "rule", "scoped"):
                s = tr[(tr.lang == lang) & (tr.rule == rule)]
                if len(s):
                    extra = ""
                    if lang == "tr":
                        over = 100 * (s.s_comma > 0).mean()
                        avoided = 100 * ((s.s_comma == 0) & (s.s_cedilla == 0)).mean()
                        extra = f" | Romanian ș inside Turkish words: {over:.1f} % | no s-letter at all: {avoided:.1f} %"
                    print(f"  {lang} {rule:7s} pass % {fmt(rate_ci(s))}{extra}")
        # word-level reading of the Turkish replies (hand-checkable lists printed below)
        tt, cls = turkish_outcomes(tr)
        for rule in ("none", "rule", "scoped"):
            x = tt[tt.rule == rule]
            share = (100 * x.outcome.value_counts(normalize=True)).round(1).to_dict()
            print(f"  tr {rule:7s} n={len(x)} | outcomes % {share}")
        allw = {k: sorted({w for c in cls for w in c[k]}) for k in ("tr_comma", "ro", "name", "unknown")}
        print("  words: Turkish with ș:", allw["tr_comma"])
        print("         Romanian:", allw["ro"])
        print("         names:", allw["name"], "| unknown:", allw["unknown"])
        tt.drop(columns=["response"]).to_csv(f"{OUT}/round2_turkish_replies.csv", index=False)
        per = tr.pivot_table(index="model", columns=["lang", "rule"], values="pass", aggfunc="mean") * 100
        per.index = [M.name(i) for i in per.index]
        print(per.round(0).to_string())
        per.to_csv(f"{OUT}/round2_turkish_models.csv")

    # ------------------------------------------------------------------ task 11
    lk = every[every.task == "lookalike"].copy()
    print("\n## Task 11: Other look-alikes")
    if len(lk):
        print("models:", lk.model.nunique(), "| answers:", len(lk))
        for v in ("clean", "cyrillic-all", "cyrillic-names", "mojibake"):
            print(f"  {v:14s} pass % {fmt(rate_ci(lk[lk.variant == v]))}")
        for kind in ("summary", "rag"):
            k = lk[lk.kind == kind]
            print(f"  {kind:8s} " + " | ".join(f"{v} {100 * k[k.variant == v]['pass'].mean():.0f}" for v in ("clean", "cyrillic-all", "cyrillic-names", "mojibake")))
        key = ["model", "run_id", "base_id", "kind"]
        piv = lk.pivot_table(index=key, columns="variant", values="pass", aggfunc="first").astype(float)
        for a, b in (("mojibake", "cyrillic-names"), ("cyrillic-all", "cyrillic-names")):
            if {a, b} <= set(piv.columns):
                n10, n01, p = mcnemar(piv[a], piv[b])
                print(f"  McNemar {a} vs {b}: {a}-only pass {n10}, {b}-only pass {n01}, p = {p:.2g}")
        per = lk.pivot_table(index="model", columns="variant", values="pass", aggfunc="mean") * 100
        if len(e4):
            ced = e4x[e4x.variant == "cedilla"].groupby("model")["pass"].mean() * 100
            for col in ("cyrillic-names", "mojibake"):
                if col in per:
                    j = pd.concat([per[col].rename("x"), ced.rename("cedilla")], axis=1).dropna()
                    print(f"  per-model Spearman({col} pass, Romanian cedilla pass) = {spearman(j.x, j.cedilla):.2f} over {len(j)} models")
        per.index = [M.name(i) for i in per.index]
        print(per.round(0).to_string())
        per.to_csv(f"{OUT}/round2_lookalike_models.csv")

    # ------------------------------------------------------------------ task 12
    tu = every[every.task == "turns"].copy()
    print("\n## Task 12: Turns")
    if len(tu):
        print("models:", tu.model.nunique(), "| conversations:", len(tu))
        for cond in ("clean>clean", "cedilla>clean", "clean>cedilla"):
            print(f"  {cond:14s} second-summary pass % {fmt(rate_ci(tu[tu.cond == cond], cluster='pair_id'))}")
        cc = tu[tu.cond == "cedilla>clean"]
        if len(cc):
            inf_first = cc[cc.first_cedilla > 0]
            print(f"  cedilla>clean: first summary had cedilla in {len(inf_first)} of {len(cc)};"
                  f" second infected when first was: {100 * (inf_first.second_cedilla > 0).mean():.0f} %,"
                  f" when first was clean: {100 * (cc[cc.first_cedilla == 0].second_cedilla > 0).mean():.0f} %")
        per = tu.pivot_table(index="model", columns="cond", values="pass", aggfunc="mean") * 100
        per.index = [M.name(i) for i in per.index]
        print(per.round(0).to_string())
        per.to_csv(f"{OUT}/round2_turns_models.csv")


if __name__ == "__main__":
    main()
