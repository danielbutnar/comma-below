"""Charts for the third version of the post: fewer words per chart, larger type for DEV's column.

Drawn 820 px wide with text of 20 px or more, so labels stay readable at DEV's 680 px column
(about 17 px) and can be zoomed on a phone. Titles state the finding; alt text carries the numbers.
Usage:  uv run --no-project --with pandas --with numpy python analysis/charts3.py
        then: node post/render.mjs post/chart-hero.html post/chart-keyboard.html
"""

from __future__ import annotations

import json
import re
import unicodedata
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
from charts import C, POST, esc  # noqa: E402
import models as M  # noqa: E402
import own_words  # noqa: E402
from round2 import ok_rows  # noqa: E402

ROOT = POST.parent
W = 820
FOOT = "Romanian Comma Below · Kaggle Benchmarks, October 2026"
RNG = np.random.default_rng(20261010)


def page3(title: str, alt: str, height: int, parts: list[str]) -> str:
    css = (f"* {{ margin: 0; box-sizing: border-box; }} body {{ background: {C['surface']}; width: {W}px; "
           f"font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }} "
           f"svg text {{ font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
           f'role="img" aria-label="{esc(alt)}">{"".join(parts)}</svg>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f"<style>{css}</style></head><body>{svg}</body></html>")


def text(x, y, s, size, fill=None, weight=400, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill or C["ink"]}" text-anchor="{anchor}">{s}</text>')


def write(file: str, title: str, alt: str, height: int, parts: list[str]):
    (POST / file).write_text(page3(title, alt, height, parts), encoding="utf-8", newline="\n")
    print("wrote", file, "|", alt)


def task8_table() -> pd.DataFrame:
    """Task 8 only (every run): share of clean answers per model and input, indexed by model, with names."""
    e4 = ok_rows(load(all_runs=True))
    e4 = e4[e4.task == "echo4"]
    t = (e4.groupby(["model", "variant"])["pass"].mean() * 100).unstack()
    t["name"] = [M.name(m) for m in t.index]
    return t


def hero_chart(pv: dict):
    """Task 8: one dot per model for each of the four inputs, pooled share as a black line."""
    t = task8_table()
    n = len(t)
    rows = [("clean", pv["E4_CLEAN"], "Typed correctly", "ș ț", C["s1"]),
            ("ascii", pv["E4_ASCII"], "Typed without diacritics", "s t", C["muted"]),
            ("cedilla", pv["E4_CED"], "Typed with the cedilla letters", "ş ţ", C["s2"]),
            ("cedilla+rule", pv["E4_RULE"], "Cedilla letters, plus one sentence", "in the system prompt", C["s3"])]
    x0, x1, band, gap, top = 40, 650, 36, 80, 196
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = "Typed with the cedilla, a third of the answers keep it"
    parts = [text(40, 52, esc(title), 29, weight=650),
             text(40, 88, f"{n} models · the same 22 Romanian prompts, typed four ways", 20, C["ink2"]),
             text(40, 116, "share of answers that use only the correct letters ș ț · one dot per model", 20, C["ink2"])]
    for i, (col, pooled, label, sub, colour) in enumerate(rows):
        y0 = top + i * (band + gap)
        mid = y0 + band / 2
        for g in (0, 25, 50, 75, 100):
            parts.append(f'<line x1="{X(g):.1f}" y1="{y0 - 2}" x2="{X(g):.1f}" y2="{y0 + band + 2}" '
                         f'stroke="{C["grid"]}" stroke-width="1.5"/>')
        parts.append(text(40, y0 - 16, f'{esc(label)} <tspan fill="{C["ink2"]}" font-weight="400">· {esc(sub)}</tspan>',
                          22, weight=600))
        vals = []
        for r in t.to_dict("records"):
            v = r[col]
            if pd.isna(v):
                continue
            vals.append((float(v), r["name"]))
            h = 0
            for ch in r["name"]:
                h = (h * 131 + ord(ch)) % 1000003
            jitter = (h % 1000) / 999 - 0.5
            parts.append(f'<circle cx="{X(v):.1f}" cy="{mid + jitter * (band - 12):.1f}" r="6" fill="{colour}" '
                         f'fill-opacity="0.75"/>')
        parts.append(f'<line x1="{X(pooled):.1f}" y1="{y0 - 5}" x2="{X(pooled):.1f}" y2="{y0 + band + 5}" '
                     f'stroke="{C["ink"]}" stroke-width="3.5"/>')
        parts.append(text(x1 + 22, mid + 10, f"{pooled} %", 28, weight=700))
        if col == "cedilla":
            lo, hi = min(vals), max(vals)
            parts.append(text(X(lo[0]), y0 + band + 26, f"{esc(lo[1])}, {lo[0]:.0f} %", 18, C["ink2"], anchor="start"))
            parts.append(text(X(hi[0]), y0 + band + 26, f"best {hi[0]:.0f} %", 18, C["ink2"], anchor="end"))
    yb = top + len(rows) * (band + gap) - gap + band + 34
    for g in (0, 50, 100):
        parts.append(text(X(g), yb, f"{g} %", 18, C["muted"], anchor="middle"))
    parts.append(text(40, yb + 40, f"{FOOT} · task 8 · black line: all answers pooled", 16, C["muted"]))
    alt = (f"{title}. {n} models, the same 22 Romanian prompts. Share of clean answers: typed correctly "
           f"{pooled_of(rows, 'clean')} %, without diacritics {pooled_of(rows, 'ascii')} %, with the cedilla letters "
           f"{pooled_of(rows, 'cedilla')} %, with the cedilla letters plus one system-prompt sentence "
           f"{pooled_of(rows, 'cedilla+rule')} %.")
    write("chart-hero.html", title, alt, yb + 64, parts)


def pooled_of(rows, col):
    return next(r[1] for r in rows if r[0] == col)


def keyboard_chart():
    """Own new words with the cedilla, by how much of my text's cedillas the answer kept."""
    a = own_words.answers(ok_rows(load(all_runs=True)))
    s = own_words.summary(a)
    n_models = a.model.nunique()
    groups = [("all", "kept all of my cedillas", C["s2"]), ("some", "kept some of them", C["base"]),
              ("none", "kept none of them", C["base"])]
    x0, x1, top, bar, gap = 330, 700, 170, 42, 40
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = "Once an answer copies my cedillas, the model's own words take them too"
    parts = [text(40, 52, esc("Once an answer copies my cedillas,"), 29, weight=650),
             text(40, 90, esc("the model's own words take them too"), 29, weight=650),
             text(40, 126, "new ș/ț words the model chose itself: share written with the cedilla", 20, C["ink2"])]
    alt_bits = []
    for i, (g, label, colour) in enumerate(groups):
        k, n, n_ans, n_mod, (lo, hi) = s[g]
        pct = 100 * k / n if n else 0
        y = top + i * (bar + gap)
        parts.append(text(40, y + 20, "When the answer", 20, C["ink2"]))
        parts.append(text(40, y + 44, esc(label), 21, weight=600))
        parts.append(f'<rect x="{x0}" y="{y}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C["grid"]}" fill-opacity="0.5"/>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{max(X(pct) - x0, 2):.1f}" height="{bar}" fill="{colour}"/>')
        parts.append(f'<line x1="{X(lo):.1f}" y1="{y + bar / 2}" x2="{X(hi):.1f}" y2="{y + bar / 2}" '
                     f'stroke="{C["ink"]}" stroke-width="2.5"/>')
        shown = f"{pct:.1f}" if 0 < pct < 1 else f"{pct:.0f}"
        parts.append(text(x1 + 18, y + bar / 2 + 10, f"{shown} %", 28, weight=700))
        parts.append(text(x1 + 18, y + bar / 2 + 34, f"{k} of {n:,}", 17, C["ink2"]))
        alt_bits.append(f"when the answer {label}, {shown} % ({k} of {n:,})")
    yb = top + len(groups) * (bar + gap) + 20
    parts.append(text(40, yb, f"Answers to text typed with the cedilla, tasks 2 and 8, {n_models} models.", 17, C["muted"]))
    parts.append(text(40, yb + 26, "Whiskers: 95 % interval, resampling models. New = not in my text, not an inflection of it.",
                      17, C["muted"]))
    parts.append(text(40, yb + 56, FOOT, 16, C["muted"]))
    alt = f"{title}. New ș/ț words written with the cedilla: " + "; ".join(alt_bits) + "."
    write("chart-keyboard.html", title, alt, yb + 80, parts)


def upgrades_chart():
    """Every version step on task 8: older version's clean share to the newer one's, significant ones in colour."""
    t = task8_table().set_index("name")
    st = pd.read_csv(ROOT / "results" / "round2_version_steps.csv")
    st = st[st.kind == "version"].copy()
    st["a"] = st.older.map(t["cedilla"])
    st["b"] = st.newer.map(t["cedilla"])
    st = st.dropna(subset=["a", "b"]).sort_values("change")
    worse, better = int(((st.p < 0.05) & (st.change < 0)).sum()), int(((st.p < 0.05) & (st.change > 0)).sum())
    x0, x1, top, row = 330, 760, 176, 38
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = f"Of {len(st)} upgrades, {worse} copied my cedillas far more often, {better} far less"
    parts = [text(40, 52, esc(f"Of {len(st)} upgrades on the same prompts, {worse} copied"), 29, weight=650),
             text(40, 90, esc(f"my cedillas far more often and {better} far less"), 29, weight=650),
             text(40, 126, "share of clean answers to text typed with the cedilla · task 8", 20, C["ink2"])]
    for g in (0, 50, 100):
        parts.append(f'<line x1="{X(g):.1f}" y1="{top - 10}" x2="{X(g):.1f}" y2="{top + len(st) * row - 10}" '
                     f'stroke="{C["grid"]}" stroke-width="1.5"/>')
        parts.append(text(X(g), top + len(st) * row + 16, f"{g} %", 18, C["muted"], anchor="middle"))
    # Holm: which changes stay significant after correcting for every comparison on the chart
    ps = sorted(st.p)
    holm_cut = next((p for k, p in enumerate(ps) if p > 0.05 / (len(ps) - k)), 1.0)
    version = lambda name: re.search(r"\d+(?:\.\d+)?", name).group(0)
    alt_bits = []
    for i, r in enumerate(st.itertuples()):
        y = top + i * row + 8
        sig, holm = r.p < 0.05, r.p < holm_cut
        colour = (C["s2"] if r.change < 0 else C["s1"]) if sig else C["base"]
        label = f"{r.line} {version(r.older)} → {version(r.newer)}"
        parts.append(text(x0 - 16, y + 7, esc(label), 20, C["ink"] if sig else C["ink2"], weight=700 if holm else 400,
                          anchor="end"))
        parts.append(f'<line x1="{X(r.a):.1f}" y1="{y}" x2="{X(r.b):.1f}" y2="{y}" stroke="{colour}" stroke-width="4"/>')
        parts.append(f'<circle cx="{X(r.a):.1f}" cy="{y}" r="6.5" fill="{C["surface"]}" stroke="{colour}" stroke-width="3"/>')
        parts.append(f'<circle cx="{X(r.b):.1f}" cy="{y}" r="7.5" fill="{colour}"/>')
        if sig:
            parts.append(text(x1 + 14, y + 7, f"{r.b - r.a:+.0f}", 20, colour, weight=700))
            alt_bits.append(f"{r.older} {r.a:.0f} % to {r.newer} {r.b:.0f} %")
    yb = top + len(st) * row + 52
    parts.append(text(40, yb, "Hollow dot: older version · filled: newer · colour: change unlikely by chance (p < 0.05)",
                      17, C["muted"]))
    parts.append(text(40, yb + 26, f"Bold: still significant after correcting for all {len(st)} comparisons (Holm)",
                      17, C["muted"]))
    parts.append(text(40, yb + 56, FOOT, 16, C["muted"]))
    alt = f"{title}. Significant changes: " + "; ".join(alt_bits) + "."
    write("chart-upgrades.html", title, alt, yb + 80, parts)


def clean(text_: str) -> bool:
    """The benchmark's pass rule for a Romanian answer: no cedilla or look-alike letter, at least one ș/ț."""
    t = unicodedata.normalize("NFC", text_ or "")
    return not any(c in t for c in "şŞţŢǎǍãÃ") and any(c in t for c in "șȘțȚ")


def fix_numbers() -> dict:
    """Romanian answers made clean and Turkish replies left intact, for each fix (prompt or code).

    Romanian: task 13 when it has runs (no rule, full rule and scoped rule on the same models and
    prompts, so the three prompt rows are like for like); otherwise task 8 for the first two rows and
    task 10's Romanian replies for the scoped one. Code fixes are applied to the no-rule answers."""
    from fix_check import fix_naive, fix_romanian  # noqa: E402
    from round2 import turkish_outcomes  # noqa: E402
    df = ok_rows(load(all_runs=True))
    tr = df[df.task == "turkish"]
    tt, _ = turkish_outcomes(tr)
    natural = tt[(tt.rule == "none") & (tt.outcome == "correct")]  # the bot's own correct Turkish replies
    w = df[df.task == "wrong"]
    if len(w) and w.model.nunique() >= 10:
        base, full, scoped = (w[w.variant == v] for v in ("cedilla", "cedilla+rule", "cedilla+scoped"))
        ro_src = f"task 13, {w.model.nunique()} models"
    else:
        base = df[(df.task == "echo4") & (df.variant == "cedilla")]
        full = df[(df.task == "echo4") & (df.variant == "cedilla+rule")]
        scoped = tr[(tr.lang == "ro") & (tr.rule == "scoped")]
        ro_src = f"task 8, {base.model.nunique()} models; scoped row: task 10 replies"
    ok = lambda rule: 100 * (tt[tt.rule == rule].outcome == "correct").mean()
    intact = lambda f: 100 * natural.response.map(lambda r: f(r) == unicodedata.normalize("NFC", r)).mean()
    return {
        "ro_src": ro_src, "tr_models": tt.model.nunique(), "tr_n": len(natural),
        "rows": [
            ("No fix", 100 * base["pass"].mean(), ok("none")),
            ("One sentence in the system prompt", 100 * full["pass"].mean(), ok("rule")),
            ("The same sentence, \"Romanian only\"", 100 * scoped["pass"].mean(), ok("scoped")),
            ("Code: swap every ş for ș", 100 * base.response.map(lambda r: clean(fix_naive(r))).mean(), intact(fix_naive)),
            ("Code: swap only outside Turkish", 100 * base.response.map(lambda r: clean(fix_romanian(r))).mean(),
             intact(fix_romanian)),
        ]}


def fix_chart():
    f = fix_numbers()
    x0, x1, top, bar, row = 40, 560, 196, 26, 112
    X = lambda p: x0 + (x1 - x0) * p / 100
    code_ro, code_tr = f["rows"][-1][1], f["rows"][-1][2]
    changed = round(f["tr_n"] * (100 - code_tr) / 100)
    title = (f"A Romanian-only swap in code cleans {'every' if round(code_ro) == 100 else f'{code_ro:.0f} % of'} "
             f"Romanian answer{'' if round(code_ro) == 100 else 's'} and changes {changed} of {f['tr_n']} Turkish replies")
    parts = [text(40, 52, "A Romanian-only swap in code cleans every" if round(code_ro) == 100 else esc(title[:40]), 29, weight=650),
             text(40, 90, f"Romanian answer and changes {changed} of {f['tr_n']} Turkish replies", 29, weight=650),
             f'<rect x="40" y="118" width="18" height="18" fill="{C["s3"]}"/>',
             text(66, 133, f"Romanian answers clean ({f['ro_src']})", 19, C["ink2"]),
             f'<rect x="40" y="146" width="18" height="18" fill="{C["s1"]}"/>',
             text(66, 161, f"Turkish replies intact (task 10, {f['tr_models']} models)", 19, C["ink2"])]
    alt_bits = []
    for i, (label, ro, trk) in enumerate(f["rows"]):
        y = top + i * row
        parts.append(text(40, y + 4, esc(label), 21, weight=600))
        for j, (v, colour) in enumerate(((ro, C["s3"]), (trk, C["s1"]))):
            yy = y + 16 + j * (bar + 6)
            parts.append(f'<rect x="{x0}" y="{yy}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C["grid"]}" fill-opacity="0.5"/>')
            parts.append(f'<rect x="{x0}" y="{yy}" width="{max(X(v) - x0, 2):.1f}" height="{bar}" fill="{colour}"/>')
            parts.append(text(x1 + 14, yy + bar - 4, f"{v:.0f} %", 23, weight=700))
        alt_bits.append(f"{label}: Romanian {ro:.0f} % clean, Turkish {trk:.0f} % intact")
    yb = top + len(f["rows"]) * row + 6
    parts.append(text(40, yb, "Prompt rows: the models' own answers under each system prompt. Code rows: the fix applied", 17, C["muted"]))
    parts.append(text(40, yb + 24, f"to the answers with no rule ({f['tr_n']} correct Turkish replies). \"Outside Turkish\": sentences without ı ğ ç ö ü.",
                      17, C["muted"]))
    parts.append(text(40, yb + 54, FOOT, 16, C["muted"]))
    alt = f"{title}. " + "; ".join(alt_bits) + "."
    write("chart-fixes.html", title, alt, yb + 78, parts)


def wrong_chart():
    """Task 13: share of the source's s/t letters that come back in the input's wrong form, per wrong form."""
    import task13 as T13  # noqa: E402
    wd = T13.prepare(ok_rows(load(all_runs=True)))
    n = wd.model.nunique()
    forms = [("cedilla", "Braşov", "the cedilla", C["s2"]), ("dot", "Braṣov", "s with a dot below", C["base"]),
             ("legacy", "Braºov", "old mojibake", C["base"])]
    x0, x1, top, bar, row = 300, 680, 190, 46, 104
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = "Of three wrong spellings, only the cedilla survives"
    parts = [text(40, 52, esc(title), 29, weight=650),
             text(40, 88, f"{n} models · the same 16 summaries and document questions", 20, C["ink2"]),
             text(40, 116, "share of the source's s and t letters that came back in the same wrong form", 20, C["ink2"])]
    alt_bits = []
    for i, (var, word, label, colour) in enumerate(forms):
        d = wd[(wd.variant == var) & (wd.sl_st > 0)]
        pct_ = 100 * d.kept.sum() / d.sl_st.sum()
        g = d.groupby("model")[["kept", "sl_st"]].sum()
        idx = RNG.integers(0, len(g), size=(4000, len(g)))
        s = g.values[idx].sum(axis=1)
        lo, hi = np.percentile(100 * s[:, 0] / s[:, 1], [2.5, 97.5])
        y = top + i * row
        parts.append(text(40, y + 34, esc(word), 38, weight=600))
        parts.append(text(40, y + 66, esc(label), 19, C["ink2"]))
        parts.append(f'<rect x="{x0}" y="{y + 4}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C["grid"]}" fill-opacity="0.5"/>')
        parts.append(f'<rect x="{x0}" y="{y + 4}" width="{max(X(pct_) - x0, 3):.1f}" height="{bar}" fill="{colour}"/>')
        parts.append(f'<line x1="{X(lo):.1f}" y1="{y + 4 + bar / 2}" x2="{X(hi):.1f}" y2="{y + 4 + bar / 2}" '
                     f'stroke="{C["ink"]}" stroke-width="2.5"/>')
        shown = f"{pct_:.1f}" if pct_ < 10 else f"{pct_:.0f}"
        parts.append(text(x1 + 18, y + 4 + bar / 2 + 10, f"{shown} %", 28, weight=700))
        alt_bits.append(f"{word} ({label}) {shown} %")
    yb = top + len(forms) * row + 10
    parts.append(text(40, yb, "Whiskers: 95 % interval, resampling models. Task 13, pre-registered on Kaggle before the runs.",
                      17, C["muted"]))
    parts.append(text(40, yb + 30, FOOT, 16, C["muted"]))
    alt = f"{title}. Share of s and t letters kept in the input's wrong form, {n} models: " + "; ".join(alt_bits) + "."
    write("chart-wrong.html", title, alt, yb + 54, parts)


def main():
    pv = json.loads((ROOT / "results" / "post_values.json").read_text(encoding="utf-8"))
    hero_chart(pv)
    keyboard_chart()
    upgrades_chart()
    fix_chart()
    wrong_chart()


if __name__ == "__main__":
    main()
