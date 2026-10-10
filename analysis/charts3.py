"""Charts for the third version of the post: fewer words per chart, larger type for DEV's column.

Drawn 820 px wide with text of 20 px or more (only the source line is smaller), so labels stay readable
at DEV's 680 px column (about 17 px) and can be zoomed on a phone. Muted text is #6f6e69, 5:1 on the
background. Titles state the finding; alt text carries the numbers and is printed when a chart is written.

DEV keeps its own copy of an image by URL, so a chart that changes after it was pasted gets a new file name
here, and the old file stays for the version of the post that still loads it. The post uses exactly the
files in OUT (chart-fixes-v4 was the earlier chart-fixes output, renamed by hand; this script now writes the
name the post uses).

Usage:  uv run --no-project --with pandas --with numpy python analysis/charts3.py
        then: node post/render.mjs post/chart-hero-v2.html post/chart-keyboard-v2.html \\
              post/chart-wrong-v2.html post/chart-upgrades-v2.html post/chart-fixes-v5.html
        (render.mjs needs playwright-core and Chrome; see the notes at its top about the font)
"""

from __future__ import annotations

import functools
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
# Darker grey than charts.py for text (4.98:1 on the background, was 3.5:1), and a grey for
# marks that are there for context (3.2:1, was 1.75:1).
C3 = dict(C, muted="#6f6e69", quiet="#8f8e85")
FONT = "'Segoe UI', Inter, system-ui, sans-serif"
OUT = {"hero": "chart-hero-v2.html", "keyboard": "chart-keyboard-v2.html", "upgrades": "chart-upgrades-v2.html",
       "fixes": "chart-fixes-v5.html", "wrong": "chart-wrong-v2.html"}


def page3(title: str, alt: str, height: int, parts: list[str]) -> str:
    css = (f"* {{ margin: 0; box-sizing: border-box; }} body {{ background: {C3['surface']}; width: {W}px; "
           f"font-family: {FONT}; }} svg text {{ font-family: {FONT}; }}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
           f'role="img" aria-label="{esc(alt)}">{"".join(parts)}</svg>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f"<style>{css}</style></head><body>{svg}</body></html>")


def text(x, y, s, size, fill=None, weight=400, anchor="start", halo=False):
    """halo: a background-coloured outline, so a label written over gridlines stays clean."""
    ring = (f' stroke="{C3["surface"]}" stroke-width="6" stroke-linejoin="round" paint-order="stroke"'
            if halo else "")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill or C3["ink"]}" text-anchor="{anchor}"{ring}>{s}</text>')


def write(key: str, title: str, alt: str, height: int, parts: list[str]):
    file = OUT[key]
    (POST / file).write_text(page3(title, alt, height, parts), encoding="utf-8", newline="\n")
    print(f"wrote {file}\n  title: {title}\n  alt: {alt}")


def pct(v: float) -> str:
    """A share as the post prints it: one decimal under 10 %, none above."""
    return f"{v:.1f}" if 0 < v < 10 else f"{v:.0f}"


def names(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


@functools.lru_cache(maxsize=1)
def rows_ok() -> pd.DataFrame:
    return ok_rows(load(all_runs=True))


def task8_table() -> pd.DataFrame:
    """Task 8 only (every run): share of clean answers per model and input, indexed by model, with names."""
    e4 = rows_ok()
    e4 = e4[e4.task == "echo4"]
    t = (e4.groupby(["model", "variant"])["pass"].mean() * 100).unstack()
    t["name"] = [M.name(m) for m in t.index]
    return t


def hero_chart(pv: dict):
    """Task 8: one dot per model for each of the four inputs, pooled share as a black line."""
    t = task8_table()
    n = len(t)
    rows = [("clean", pv["E4_CLEAN"], "Typed correctly", "ș ț", C3["s1"]),
            ("ascii", pv["E4_ASCII"], "Typed without diacritics", "s t", C3["muted"]),
            ("cedilla", pv["E4_CED"], "Typed with the cedilla letters", "ş ţ", C3["s2"]),
            ("cedilla+rule", pv["E4_RULE"], "Cedilla letters, plus one sentence", "in the system prompt", C3["s3"])]
    x0, x1, band, gap, top = 48, 650, 36, 86, 226
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = "Typed with the cedilla, a third of the answers keep it"
    parts = [text(40, 52, esc(title), 29, weight=650),
             text(40, 88, f"{n} models · the same 22 Romanian prompts, typed four ways", 20, C3["ink2"]),
             text(40, 116, "share of clean answers: with ș or ț, and no cedilla or look-alike letter", 20, C3["ink2"]),
             text(40, 144, "one dot per model · black line and number: all answers pooled", 20, C3["muted"])]
    notes = []
    for i, (col, pooled, label, sub, colour) in enumerate(rows):
        y0 = top + i * (band + gap)
        mid = y0 + band / 2
        for g in (0, 25, 50, 75, 100):
            parts.append(f'<line x1="{X(g):.1f}" y1="{y0 - 2}" x2="{X(g):.1f}" y2="{y0 + band + 2}" '
                         f'stroke="{C3["grid"]}" stroke-width="1.5"/>')
        parts.append(text(40, y0 - 16, f'{esc(label)} <tspan fill="{C3["ink2"]}" font-weight="400">· {esc(sub)}</tspan>',
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
                     f'stroke="{C3["ink"]}" stroke-width="3.5"/>')
        parts.append(text(x1 + 22, mid + 10, f"{pooled} %", 28, weight=700))
        below = y0 + band + 28
        at100 = sum(v >= 99.95 for v, _ in vals)
        if at100 >= 5:  # a pile at 100 % reads as one dot, so say how many it is
            parts.append(text(X(100), below, f"{at100} of {len(vals)} at 100 %", 20, C3["muted"], anchor="end",
                              halo=True))
        if col == "clean":  # the few models that put a cedilla into text typed correctly
            lo = min(v for v, _ in vals)
            odd = sorted(nm for v, nm in vals if v < 90)
            if odd and all(f"{v:.0f}" == f"{lo:.0f}" for v, nm in vals if v < 90):
                parts.append(text(X(lo) - 12, mid + 7, f"{esc(names(odd))}, {lo:.0f} %", 20, C3["ink2"], anchor="end",
                                  halo=True))
                notes.append(f"typed correctly, {names(odd)} kept {lo:.0f} % clean")
        if col == "cedilla":
            lo, hi = min(vals), max(v for v, _ in vals)
            best = [nm for v, nm in sorted(vals, key=lambda x: x[1]) if v == hi]
            parts.append(text(X(lo[0]) - 12, mid + 7, f"{esc(lo[1])}, {lo[0]:.0f} %", 20, C3["ink2"], anchor="end",
                              halo=True))
            parts.append(text(X(hi) + 7, below, f"{esc(names(best))}, {hi:.0f} %", 20, C3["ink2"], anchor="end",
                              halo=True))
            notes.append(f"typed with the cedilla, the best were {names(best)} at {hi:.0f} %, "
                         f"the lowest {lo[1]} at {lo[0]:.0f} %")
    yb = top + len(rows) * (band + gap) - gap + band + 34
    for g in (0, 50, 100):
        parts.append(text(X(g), yb + 12, f"{g} %", 20, C3["muted"], anchor="middle"))
    parts.append(text(40, yb + 56, f"{FOOT} · task 8", 16, C3["muted"]))
    notes = "; ".join(notes)
    alt = (f"{title}. {n} models, the same 22 Romanian prompts. Share of clean answers (with ș or ț, and no cedilla "
           f"or look-alike letter): typed correctly {pooled_of(rows, 'clean')} %, without diacritics "
           f"{pooled_of(rows, 'ascii')} %, with the cedilla letters {pooled_of(rows, 'cedilla')} %, with the cedilla "
           f"letters plus one system-prompt sentence {pooled_of(rows, 'cedilla+rule')} %. {notes[:1].upper()}{notes[1:]}.")
    write("hero", title, alt, yb + 82, parts)


def pooled_of(rows, col):
    return next(r[1] for r in rows if r[0] == col)


def keyboard_chart():
    """Own new words with the cedilla, by how much of my text's cedillas the answer kept."""
    a = own_words.answers(rows_ok())
    s = own_words.summary(a)
    n_models = a.model.nunique()
    task2_only = sorted(M.name(m) for m in set(a.model) - set(a[a.task == "echo4"].model))
    groups = [("all", "kept all of my cedillas", C3["s2"]), ("some", "kept some of them", C3["quiet"]),
              ("none", "kept none of them", C3["quiet"])]
    x0, x1, top, bar, gap = 330, 680, 194, 42, 46
    X = lambda p: x0 + (x1 - x0) * p / 100
    k_all, n_all = s["all"][:2]
    head = f"When an answer kept all my cedillas, {pct(100 * k_all / n_all)} % of"
    tail = "the new ș/ț words it added had the cedilla too"
    title = f"{head} {tail}"
    parts = [text(40, 52, esc(head), 29, weight=650),
             text(40, 90, esc(tail), 29, weight=650),
             text(40, 128, "new word: not in my text, and not an inflection of a word in it", 20, C3["ink2"])]
    alt_bits = []
    for i, (g, label, colour) in enumerate(groups):
        k, n, n_ans, n_mod, (lo, hi) = s[g]
        p = 100 * k / n if n else 0
        y = top + i * (bar + gap)
        parts.append(text(40, y + 18, "When the answer", 20, C3["ink2"]))
        parts.append(text(40, y + 44, esc(label), 22, weight=600))
        parts.append(f'<rect x="{x0}" y="{y}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C3["grid"]}" fill-opacity="0.5"/>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{max(X(p) - x0, 2):.1f}" height="{bar}" fill="{colour}"/>')
        parts.append(f'<line x1="{X(lo):.1f}" y1="{y + bar / 2}" x2="{X(hi):.1f}" y2="{y + bar / 2}" '
                     f'stroke="{C3["ink"]}" stroke-width="2.5"/>')
        parts.append(text(x1 + 18, y + bar / 2 + 8, f"{pct(p)} %", 28, weight=700))
        parts.append(text(x1 + 18, y + bar / 2 + 34, f"{k} of {n:,}", 20, C3["ink2"]))
        alt_bits.append(f"when the answer {label}, {pct(p)} % ({k} of {n:,})")
    yb = top + len(groups) * (bar + gap) + 16
    who = f" ({names(task2_only)}: task 2 only)" if task2_only else ""
    parts.append(text(40, yb, f"Answers to text typed with the cedilla, tasks 2 and 8, {n_models} models", 20, C3["muted"]))
    parts.append(text(40, yb + 28, f"{esc(who.strip())}{'. ' if who else ''}Whiskers: 95 % interval, resampling models.",
                      20, C3["muted"]))
    parts.append(text(40, yb + 60, FOOT, 16, C3["muted"]))
    alt = (f"{title}. Share of the new ș/ț words (not in my text, not an inflection of a word in it) written with "
           f"the cedilla: " + "; ".join(alt_bits) + f". Tasks 2 and 8, {n_models} models.")
    write("keyboard", title, alt, yb + 84, parts)


def pooled_cedilla() -> pd.Series:
    """Clean share on cedilla input per model name, every run of the same 22 prompts: task 8, plus task 2 for
    the round-one models. This is how round2.py pools them for the version-step test in
    results/round2_version_steps.csv, so the dots and the test use the same answers."""
    every = rows_ok()
    e4 = every[every.task == "echo4"]
    r1 = every[every.task.isin(["echo", "rule"]) & every.model.isin(set(e4.model))]
    e4x = pd.concat([e4, r1[[c for c in e4.columns if c in r1.columns]]], ignore_index=True)
    rate = e4x[e4x.variant == "cedilla"].groupby("model")["pass"].mean() * 100
    return pd.Series({M.name(m): v for m, v in rate.items()})


def holm(p: pd.Series, alpha: float = 0.05) -> pd.Series:
    """Holm-Bonferroni, as analysis/check_claims.py applies it: True where the change survives."""
    keep = pd.Series(False, index=p.index)
    for i, (ix, v) in enumerate(p.sort_values().items()):
        if v > alpha / (len(p) - i):
            break
        keep[ix] = True
    return keep


def arrow(x: float, y: float, d: int) -> str:
    """Points of an arrowhead whose tip is at (x, y), pointing right (d=1) or left (d=-1)."""
    return f"{x:.1f},{y:.1f} {x - d * 12:.1f},{y - 7:.1f} {x - d * 12:.1f},{y + 7:.1f}"


def upgrades_chart():
    """Every version step: older version's clean share to the newer one's, the changes that survive Holm in colour."""
    rate = pooled_cedilla()
    st = pd.read_csv(ROOT / "results" / "round2_version_steps.csv")
    st = st[st.kind == "version"].copy()
    st["a"] = st.older.map(rate)
    st["b"] = st.newer.map(rate)
    st = st.dropna(subset=["a", "b"])
    gap = (st.b - st.a - st.change).abs().max()
    assert gap < 0.01, f"the dots and the tested change differ by {gap:.2f} points: rerun analysis/round2.py"
    st["holm"] = holm(st.p)
    st = st.sort_values(["change", "line"])
    m = len(st)
    worse, better = int((st.holm & (st.change < 0)).sum()), int((st.holm & (st.change > 0)).sum())
    lo_x = 40 if st[["a", "b"]].min().min() >= 45 else 0
    x0, x1, top, row = 330, 680, 252, 34
    X = lambda p: x0 + (x1 - x0) * (p - lo_x) / (100 - lo_x)
    count = lambda k: "none" if k == 0 else str(k)
    head = f"Of {m} upgrades on the same prompts, {count(worse)} copied"
    tail = f"my cedillas far more often, and {count(better)} far less"
    title = f"{head} {tail}"
    parts = [text(40, 52, esc(head), 29, weight=650),
             text(40, 90, esc(tail), 29, weight=650),
             text(40, 128, "share of clean answers to text typed with the cedilla, every run of", 20, C3["ink2"]),
             text(40, 154, "the same 22 prompts (task 8, and task 2 for the first-round models)", 20, C3["ink2"])]
    # key: hollow dot, arrow, filled dot
    ky = 190
    parts.append(f'<circle cx="48" cy="{ky - 7}" r="6.5" fill="{C3["surface"]}" stroke="{C3["ink2"]}" stroke-width="3"/>')
    parts.append(text(62, ky, "older version", 20, C3["muted"]))
    parts.append(f'<line x1="196" y1="{ky - 7}" x2="236" y2="{ky - 7}" stroke="{C3["ink2"]}" stroke-width="4"/>')
    parts.append(f'<polygon points="{arrow(244, ky - 7, 1)}" fill="{C3["ink2"]}"/>')
    parts.append(f'<circle cx="252" cy="{ky - 7}" r="7.5" fill="{C3["ink2"]}"/>')
    parts.append(text(268, ky, "newer · colour: beyond chance after", 20, C3["muted"]))
    parts.append(text(40, ky + 28, f"correcting for all {m} comparisons (sign-flip test over the prompts, Holm)",
                      20, C3["muted"]))
    ticks = [50, 75, 100] if lo_x else [0, 50, 100]
    for g in ticks:
        parts.append(f'<line x1="{X(g):.1f}" y1="{top - 14}" x2="{X(g):.1f}" y2="{top + m * row - 14}" '
                     f'stroke="{C3["grid"]}" stroke-width="1.5"/>')
        parts.append(text(X(g), top + m * row + 12, f"{g} %", 20, C3["muted"], anchor="middle"))
    version = lambda name: re.search(r"\d+(?:\.\d+)?", name).group(0)
    alt_bits = []
    for i, r in enumerate(st.itertuples()):
        y = top + i * row
        colour = (C3["s2"] if r.change < 0 else C3["s1"]) if r.holm else C3["quiet"]
        label = f"{r.line} {version(r.older)} → {version(r.newer)}"
        parts.append(text(x0 - 16, y + 7, esc(label), 20, C3["ink"] if r.holm else C3["ink2"],
                          weight=700 if r.holm else 400, anchor="end"))
        xa, xb = X(r.a), X(r.b)
        d = 1 if xb >= xa else -1
        if abs(xb - xa) >= 36:  # long enough for an arrowhead that stops at the newer dot
            parts.append(f'<line x1="{xa:.1f}" y1="{y}" x2="{xb - d * 14:.1f}" y2="{y}" stroke="{colour}" stroke-width="4"/>')
            parts.append(f'<polygon points="{arrow(xb - d * 7, y, d)}" fill="{colour}"/>')
        else:
            parts.append(f'<line x1="{xa:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}" stroke="{colour}" stroke-width="4"/>')
        parts.append(f'<circle cx="{xa:.1f}" cy="{y}" r="6.5" fill="{C3["surface"]}" stroke="{colour}" stroke-width="3"/>')
        parts.append(f'<circle cx="{xb:.1f}" cy="{y}" r="7.5" fill="{colour}"/>')
        parts.append(text(W - 16, y + 7, f"{r.a:.0f} → {r.b:.0f}", 20, colour if r.holm else C3["ink2"],
                          weight=700 if r.holm else 400, anchor="end"))
        if r.holm:
            alt_bits.append(f"{r.older} {r.a:.0f} % to {r.newer.replace('Claude ', '')} {r.b:.0f} %")
    yb = top + m * row + 52
    parts.append(text(40, yb, "Numbers on the right: share clean, older → newer version.", 20, C3["muted"]))
    parts.append(text(40, yb + 30, FOOT, 16, C3["muted"]))
    others = m - worse - better
    alt = (f"{title}. Share of clean answers to text typed with the cedilla, every run of the same 22 prompts. "
           f"Changes beyond chance after correcting for all {m} comparisons: " + "; ".join(alt_bits) +
           f". The other {others} changes don't survive the correction.")
    write("upgrades", title, alt, yb + 54, parts)


def clean(text_: str) -> bool:
    """The benchmark's pass rule for a Romanian answer: no cedilla or look-alike letter, at least one ș/ț."""
    t = unicodedata.normalize("NFC", text_ or "")
    return not any(c in t for c in "şŞţŢǎǍãÃ") and any(c in t for c in "șȘțȚ")


def fix_numbers() -> dict:
    """Romanian answers made clean and Turkish replies still correct, for each fix (prompt or code).

    Romanian: task 13 when it has runs (no rule, full rule and scoped rule on the same models and
    prompts, so the three prompt rows are like for like); otherwise task 8 for the first two rows and
    task 10's Romanian replies for the scoped one. Code fixes are applied to the no-rule answers; a
    Turkish reply is still correct when the code leaves it unchanged."""
    from fix_check import fix_naive, fix_romanian  # noqa: E402
    from round2 import turkish_outcomes  # noqa: E402
    df = rows_ok()
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
            ("The same sentence, “Romanian only”", 100 * scoped["pass"].mean(), ok("scoped")),
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
    head = ("A Romanian-only swap in code cleans every" if round(code_ro) == 100 else
            f"A Romanian-only swap in code cleans {code_ro:.0f} % of")
    tail = (f"Romanian answer{'' if round(code_ro) == 100 else 's'} and changes {changed} of {f['tr_n']} "
            f"Turkish replies")
    title = f"{head} {tail}"
    ro_c, tr_c = C3["s3"], C3["ink2"]
    parts = [text(40, 52, esc(head), 28, weight=650),  # 28 px: the second line is the longest title line
             text(40, 90, esc(tail), 28, weight=650),
             f'<rect x="40" y="117" width="20" height="20" fill="{ro_c}"/>',
             text(70, 134, f"RO: Romanian answers clean ({f['ro_src']})", 20, C3["ink2"]),
             f'<rect x="40" y="146" width="20" height="20" fill="{tr_c}"/>',
             text(70, 163, f"TR: Turkish replies still correct (task 10, {f['tr_models']} models)", 20, C3["ink2"])]
    alt_bits = []
    for i, (label, ro, trk) in enumerate(f["rows"]):
        y = top + i * row
        parts.append(text(40, y + 4, esc(label), 21, weight=600))
        for j, (v, colour, tag) in enumerate(((ro, ro_c, "RO"), (trk, tr_c, "TR"))):
            yy = y + 16 + j * (bar + 6)
            parts.append(f'<rect x="{x0}" y="{yy}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C3["grid"]}" fill-opacity="0.5"/>')
            parts.append(f'<rect x="{x0}" y="{yy}" width="{max(X(v) - x0, 2):.1f}" height="{bar}" fill="{colour}"/>')
            parts.append(text(x1 + 14, yy + bar - 4, f'<tspan font-weight="400" fill="{C3["ink2"]}">{tag}</tspan> {v:.0f} %',
                              23, weight=700))
        alt_bits.append(f"{label}: Romanian {ro:.0f} % clean, Turkish {trk:.0f} % still correct")
    yb = top + len(f["rows"]) * row + 6
    parts.append(text(40, yb, "Prompt rows: the models’ own answers under each system prompt.", 20, C3["muted"]))
    parts.append(text(40, yb + 28, "Code rows: the fix applied to the answers given with no rule", 20, C3["muted"]))
    parts.append(text(40, yb + 56, f"({f['tr_n']} correct Turkish replies). “Outside Turkish”: sentences without ı ğ ç ö ü.",
                      20, C3["muted"]))
    parts.append(text(40, yb + 88, FOOT, 16, C3["muted"]))
    alt = f"{title}. " + "; ".join(alt_bits) + "."
    write("fixes", title, alt, yb + 112, parts)


def wrong_chart():
    """Task 13: of the ș/ț letters in the words an answer reused from the source, the share that came back in
    the input's wrong form (src/build.py slots13 counts only those letters)."""
    import task13 as T13  # noqa: E402
    wd = T13.prepare(rows_ok())
    n = wd.model.nunique()
    forms = [("cedilla", "Braşov", "with the cedilla", C3["s2"]), ("dot", "Braṣov", "with a dot below", C3["quiet"]),
             ("legacy", "Braºov", "as old mojibake", C3["quiet"])]
    x0, x1, top, bar, row = 300, 640, 196, 46, 104
    X = lambda p: x0 + (x1 - x0) * p / 100
    title = "Of three wrong spellings, only the cedilla survives"
    parts = [text(40, 52, esc(title), 29, weight=650),
             text(40, 88, f"{n} models · the same 16 summaries and document questions", 20, C3["ink2"]),
             text(40, 116, "of the ș and ț letters in words the answers reused from my text,", 20, C3["ink2"]),
             text(40, 144, "the share that came back in the same wrong form", 20, C3["ink2"])]
    alt_bits = []
    for i, (var, word, label, colour) in enumerate(forms):
        d = wd[(wd.variant == var) & (wd.sl_st > 0)]
        k, tot = int(d.kept.sum()), int(d.sl_st.sum())
        p = 100 * k / tot
        g = d.groupby("model")[["kept", "sl_st"]].sum()
        idx = RNG.integers(0, len(g), size=(4000, len(g)))
        s = g.values[idx].sum(axis=1)
        lo, hi = np.percentile(100 * s[:, 0] / s[:, 1], [2.5, 97.5])
        y = top + i * row
        parts.append(text(40, y + 34, esc(word), 38, weight=600))
        parts.append(text(40, y + 66, esc(label), 20, C3["ink2"]))
        parts.append(f'<rect x="{x0}" y="{y + 4}" width="{X(100) - x0:.1f}" height="{bar}" fill="{C3["grid"]}" fill-opacity="0.5"/>')
        parts.append(f'<rect x="{x0}" y="{y + 4}" width="{max(X(p) - x0, 3):.1f}" height="{bar}" fill="{colour}"/>')
        parts.append(f'<line x1="{X(lo):.1f}" y1="{y + 4 + bar / 2}" x2="{X(hi):.1f}" y2="{y + 4 + bar / 2}" '
                     f'stroke="{C3["ink"]}" stroke-width="2.5"/>')
        parts.append(text(x1 + 18, y + bar / 2 + 12, f"{pct(p)} %", 28, weight=700))
        parts.append(text(x1 + 18, y + bar / 2 + 38, f"{k:,} of {tot:,}", 20, C3["ink2"]))
        alt_bits.append(f"{pct(p)} % {'came back ' if not i else ''}{label} ({word})")
    yb = top + len(forms) * row + 10
    parts.append(text(40, yb, "Whiskers: 95 % interval, resampling models.", 20, C3["muted"]))
    parts.append(text(40, yb + 28, "Task 13, pre-registered on Kaggle before the runs.", 20, C3["muted"]))
    parts.append(text(40, yb + 60, FOOT, 16, C3["muted"]))
    alt = (f"{title}. {n} models, the same 16 summaries and document questions. Of the ș and ț letters in words the "
           f"answers reused from my text, {names(alt_bits)}.")
    write("wrong", title, alt, yb + 84, parts)


def main():
    pv = json.loads((ROOT / "results" / "post_values.json").read_text(encoding="utf-8"))
    hero_chart(pv)
    keyboard_chart()
    upgrades_chart()
    fix_chart()
    wrong_chart()


if __name__ == "__main__":
    main()
