"""Build the post's charts as standalone HTML/SVG files in post/, then render
them with `node post/render.mjs post/chart-*.html`.

Usage:  uv run --no-project --with pandas python analysis/charts.py
"""

from __future__ import annotations

import csv
import html
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
POST = ROOT / "post"

NAMES = {
    "claude-opus-5-default": "Claude Opus 5",
    "claude-sonnet-5-default": "Claude Sonnet 5",
    "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "gemini-3.8-flash": "Gemini 3.8 Flash",
    "gemini-3.7-flash": "Gemini 3.7 Flash",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
    "gemma-4-31b-it": "Gemma 4 31B",
    "gpt-6-astra": "GPT-6 Astra",
    "gpt-5.5-2026-04-23": "GPT-5.5",
    "gpt-5.4-nano-2026-03-17": "GPT-5.4 nano",
    "gpt-oss-120b": "gpt-oss-120b",
    "grok-4.20-0309-reasoning": "Grok 4.20 Reasoning",
    "deepseek-r1-0528": "DeepSeek-R1",
    "qwen3-235b-a22b-instruct-2507": "Qwen 3 235B",
    "glm-5": "GLM-5",
}

# Palette: reference categorical slots 1-2 (validated), chrome from the reference instance.
C = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
         base="#c3c2b7", s1="#2a78d6", s2="#eb6834", s3="#1baf7a")

CSS = f"""
* {{ margin: 0; box-sizing: border-box; }}
body {{ background: {C['surface']}; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
       color: {C['ink']}; width: 1000px; }}
svg text {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def page(title: str, svg: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f"<style>{CSS}</style></head><body>{svg}</body></html>")


def dumbbell(rows, a_key, b_key, a_label, b_label, title, subtitle, note, file, label_b=True, c_key=None, c_label=None):
    """rows: list of dicts with name, a (0-100), b (0-100). Sorted by caller."""
    W, left, right = 1000, 250, 70
    top, row_h = 150, 34
    H = top + row_h * len(rows) + 70
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'role="img" aria-label="{esc(title)}">']
    parts.append(f'<text x="40" y="46" font-size="24" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>')
    parts.append(f'<text x="40" y="74" font-size="15" fill="{C["ink2"]}">{esc(subtitle)}</text>')
    # legend
    lx = 40
    legend = [(C["s1"], a_label), (C["s2"], b_label)] + ([(C["s3"], c_label)] if c_key else [])
    for color, label in legend:
        parts.append(f'<circle cx="{lx + 6}" cy="104" r="6" fill="{color}"/>')
        parts.append(f'<text x="{lx + 18}" y="109" font-size="14" fill="{C["ink2"]}">{esc(label)}</text>')
        lx += 30 + 7.4 * len(label)
    # grid
    for v in (0, 25, 50, 75, 100):
        parts.append(f'<line x1="{X(v):.1f}" y1="{top - 14}" x2="{X(v):.1f}" y2="{top + row_h * len(rows) - 10}" '
                     f'stroke="{C["grid"]}" stroke-width="1"/>')
        parts.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 10}" font-size="13" '
                     f'fill="{C["muted"]}" text-anchor="middle">{v}%</text>')
    for i, r in enumerate(rows):
        y = top + i * row_h + 6
        a, b = r[a_key], r[b_key]
        cv = r.get(c_key) if c_key else None
        parts.append(f'<text x="{left - 16}" y="{y + 5}" font-size="15" fill="{C["ink"]}" '
                     f'text-anchor="end">{esc(r["name"])}</text>')
        if pd.notna(a) and pd.notna(b):
            parts.append(f'<line x1="{X(min(a, b)):.1f}" y1="{y}" x2="{X(max(a, b)):.1f}" y2="{y}" '
                         f'stroke="{C["base"]}" stroke-width="2" stroke-linecap="round"/>')
        lo, hi = r.get("b_lo"), r.get("b_hi")
        if lo is not None and hi is not None and pd.notna(lo) and pd.notna(hi) and hi > lo:
            parts.append(f'<line x1="{X(lo):.1f}" y1="{y}" x2="{X(hi):.1f}" y2="{y}" stroke="{C["s2"]}" '
                         f'stroke-width="6" stroke-linecap="round" opacity="0.28"/>')
        if cv is not None and pd.notna(cv) and pd.notna(b):
            parts.append(f'<line x1="{X(min(b, cv)):.1f}" y1="{y}" x2="{X(max(b, cv)):.1f}" y2="{y}" '
                         f'stroke="{C["s3"]}" stroke-width="2" stroke-dasharray="0" opacity="0.55"/>')
        for v, color in ((a, C["s1"]), (cv, C["s3"]), (b, C["s2"])):
            if pd.notna(v):
                parts.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="6" fill="{color}" '
                             f'stroke="{C["surface"]}" stroke-width="2"/>')
        if label_b and pd.notna(b):
            anchor, dx = ("end", -12) if (pd.isna(a) or b <= a) else ("start", 12)
            edge = b
            if lo is not None and pd.notna(lo) and anchor == "end":
                edge = min(b, lo)
            parts.append(f'<text x="{X(edge) + dx:.1f}" y="{y + 5}" font-size="13" fill="{C["ink2"]}" '
                         f'text-anchor="{anchor}">{b:.0f}%</text>')
    parts.append(f'<text x="40" y="{H - 22}" font-size="13" fill="{C["muted"]}">{esc(note)}</text>')
    parts.append("</svg>")
    (POST / file).write_text(page(title, "".join(parts)), encoding="utf-8", newline="\n")
    print("wrote", file)


def paired_bars(rows, a_key, b_key, a_label, b_label, title, subtitle, note, file):
    """Two thin bars per row (a above b), value at each bar tip."""
    W, left, right = 1000, 250, 80
    top, row_h, bar = 150, 44, 12
    H = top + row_h * len(rows) + 60
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="{esc(title)}">',
         f'<text x="40" y="46" font-size="24" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>',
         f'<text x="40" y="74" font-size="15" fill="{C["ink2"]}">{esc(subtitle)}</text>']
    lx = 40
    for color, label in ((C["s1"], a_label), (C["s2"], b_label)):
        p.append(f'<rect x="{lx}" y="98" width="14" height="12" rx="3" fill="{color}"/>')
        p.append(f'<text x="{lx + 22}" y="109" font-size="14" fill="{C["ink2"]}">{esc(label)}</text>')
        lx += 36 + 7.4 * len(label)
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line x1="{X(v):.1f}" y1="{top - 12}" x2="{X(v):.1f}" y2="{top + row_h * len(rows) - 8}" '
                 f'stroke="{C["grid"]}" stroke-width="1"/>')
        p.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 12}" font-size="13" fill="{C["muted"]}" '
                 f'text-anchor="middle">{v}%</text>')
    for i, r in enumerate(rows):
        y = top + i * row_h
        p.append(f'<text x="{left - 16}" y="{y + bar + 4}" font-size="15" fill="{C["ink"]}" '
                 f'text-anchor="end">{esc(r["name"])}</text>')
        for j, (key, color) in enumerate(((a_key, C["s1"]), (b_key, C["s2"]))):
            v = r[key]
            if pd.isna(v):
                continue
            yy = y + j * (bar + 2)
            w = X(v) - x0
            if w >= 4:
                p.append(f'<path d="M{x0},{yy} h{w - 4:.1f} a4,4 0 0 1 4,4 v{bar - 8} a4,4 0 0 1 -4,4 '
                         f'h{-(w - 4):.1f} z" fill="{color}"/>')
            if v < 99.5:
                p.append(f'<text x="{X(v) + 8:.1f}" y="{yy + bar - 2}" font-size="12.5" fill="{C["ink2"]}">{v:.0f}%</text>')
    p.append(f'<text x="40" y="{H - 20}" font-size="13" fill="{C["muted"]}">{esc(note)}</text>')
    p.append("</svg>")
    (POST / file).write_text(page(title, "".join(p)), encoding="utf-8", newline="\n")
    print("wrote", file)


def echo_chart(rows, file):
    """Cedilla input (mean, range) -> same input with the rule; clean input as a 100% reference line."""
    W, left, right = 1000, 250, 70
    top, row_h = 168, 34
    H = top + row_h * len(rows) + 74
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    title = "Clean in, clean out. Cedilla in, cedilla out."
    sub = "Share of answers that use only correct ș/ț letters · 22 prompts per condition"
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="{esc(title)}">',
         f'<text x="40" y="46" font-size="24" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>',
         f'<text x="40" y="74" font-size="15" fill="{C["ink2"]}">{esc(sub)}</text>']
    lx = 40
    for kind, color, label in (("dot", C["s2"], "Text typed with cedilla (ş ţ): mean of 3 runs, shaded = range"),
                               ("dot", C["s3"], "Same text + one sentence in the system prompt")):
        p.append(f'<circle cx="{lx + 6}" cy="104" r="6" fill="{color}"/>')
        p.append(f'<text x="{lx + 18}" y="109" font-size="14" fill="{C["ink2"]}">{esc(label)}</text>')
        lx += 30 + 7.1 * len(label)
    p.append(f'<line x1="40" y1="130" x2="56" y2="130" stroke="{C["s1"]}" stroke-width="2"/>')
    p.append(f'<text x="64" y="135" font-size="14" fill="{C["ink2"]}">Clean input (ș ț): 100% for every model, in all 45 runs</text>')
    for v in (0, 25, 50, 75):
        p.append(f'<line x1="{X(v):.1f}" y1="{top - 14}" x2="{X(v):.1f}" y2="{top + row_h * len(rows) - 10}" '
                 f'stroke="{C["grid"]}" stroke-width="1"/>')
    p.append(f'<line x1="{X(100):.1f}" y1="{top - 14}" x2="{X(100):.1f}" y2="{top + row_h * len(rows) - 10}" '
             f'stroke="{C["s1"]}" stroke-width="2"/>')
    for v in (0, 25, 50, 75, 100):
        p.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 10}" font-size="13" fill="{C["muted"]}" '
                 f'text-anchor="middle">{v}%</text>')
    for i, r in enumerate(rows):
        y = top + i * row_h + 6
        b, lo, hi, q = r["echo_mean"], r["echo_min"], r["echo_max"], r.get("echo_rule")
        p.append(f'<text x="{left - 16}" y="{y + 5}" font-size="15" fill="{C["ink"]}" text-anchor="end">{esc(r["name"])}</text>')
        if pd.notna(q):
            p.append(f'<line x1="{X(b):.1f}" y1="{y}" x2="{X(q):.1f}" y2="{y}" stroke="{C["base"]}" stroke-width="2" '
                     f'stroke-linecap="round"/>')
        if pd.notna(lo) and pd.notna(hi) and hi > lo:
            p.append(f'<line x1="{X(lo):.1f}" y1="{y}" x2="{X(hi):.1f}" y2="{y}" stroke="{C["s2"]}" stroke-width="6" '
                     f'stroke-linecap="round" opacity="0.28"/>')
        p.append(f'<circle cx="{X(b):.1f}" cy="{y}" r="6" fill="{C["s2"]}" stroke="{C["surface"]}" stroke-width="2"/>')
        edge = min(b, lo) if pd.notna(lo) else b
        p.append(f'<text x="{X(edge) - 12:.1f}" y="{y + 5}" font-size="13" fill="{C["ink2"]}" text-anchor="end">{b:.0f}%</text>')
        if pd.notna(q):
            p.append(f'<circle cx="{X(q):.1f}" cy="{y}" r="6" fill="{C["s3"]}" stroke="{C["surface"]}" stroke-width="2"/>')
            if q < 99.5:
                p.append(f'<text x="{X(q) + 12:.1f}" y="{y + 5}" font-size="13" fill="{C["ink2"]}">{q:.0f}%</text>')
    p.append(f'<text x="40" y="{H - 22}" font-size="13" fill="{C["muted"]}">Romanian Comma Below 2: Echo and 7: Echo With a Rule '
             f'· Kaggle Benchmarks, 30 Sep – 1 Oct 2026 · unlabeled green dots are 100%</text>')
    p.append("</svg>")
    (POST / file).write_text(page(title, "".join(p)), encoding="utf-8", newline=chr(10))
    print("wrote", file)


def census_chart():
    rows = []
    with (ROOT / "analysis" / "web_census.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["cedilla_share"] not in ("", None):
                rows.append((r["url"].split("//")[1].split("/")[0].removeprefix("www."), 100 * float(r["cedilla_share"])))
    rows.sort(key=lambda t: -t[1])
    n_with = sum(1 for _, v in rows if v > 0)
    W, left, right, top, row_h = 1000, 220, 80, 120, 21
    H = top + row_h * len(rows) + 60
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    title = f"{n_with} of {len(rows)} Romanian front pages contain cedilla letters"
    sub = "Share of s/t-with-diacritic letters written with a cedilla (ş ţ) instead of the comma below (ș ț)"
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="{esc(title)}">',
         f'<text x="40" y="46" font-size="24" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>',
         f'<text x="40" y="74" font-size="15" fill="{C["ink2"]}">{esc(sub)}</text>']
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line x1="{X(v):.1f}" y1="{top - 12}" x2="{X(v):.1f}" y2="{top + row_h * len(rows) - 6}" '
                 f'stroke="{C["grid"]}" stroke-width="1"/>')
        p.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 12}" font-size="13" fill="{C["muted"]}" '
                 f'text-anchor="middle">{v}%</text>')
    for i, (site, v) in enumerate(rows):
        y = top + i * row_h
        p.append(f'<text x="{left - 14}" y="{y + 4}" font-size="13.5" fill="{C["ink"]}" text-anchor="end">{esc(site)}</text>')
        if v > 0:
            w = max(X(v) - x0, 4)
            p.append(f'<path d="M{x0},{y - 5} h{w - 3} a3,3 0 0 1 3,3 v4 a3,3 0 0 1 -3,3 h{-(w - 3)} z" fill="{C["s2"]}"/>')
        label = f"{v:.0f}%" if v >= 1 or v == 0 else "<1%"
        p.append(f'<text x="{X(v) + 8:.1f}" y="{y + 4}" font-size="12.5" fill="{C["ink2"]}">{label}</text>')
    p.append(f'<text x="40" y="{H - 18}" font-size="13" fill="{C["muted"]}">Front page HTML fetched once per site on '
             f'30 Sep 2026, entities decoded, scripts and styles removed. Source: analysis/web_census.py</text>')
    p.append("</svg>")
    (POST / "chart-web-census.html").write_text(page(title, "".join(p)), encoding="utf-8", newline="\n")
    print("wrote chart-web-census.html")


def main():
    s = pd.read_csv(ROOT / "results" / "summary.csv")
    s = s[s.model.isin(NAMES) & (s.model != "gpt-oss-120b")].copy()
    s["name"] = s.model.map(NAMES)

    echo = s.dropna(subset=["echo_mean"]).sort_values(["echo_mean", "name"], ascending=[False, True]).copy()
    echo["b_lo"], echo["b_hi"] = echo["echo_min"], echo["echo_max"]
    echo_chart(echo.to_dict("records"), "chart-echo.html")

    see = s.dropna(subset=["see_same_identical"]).sort_values(["see_same_identical", "name"], ascending=[True, True])
    paired_bars(see.to_dict("records"), "see_same_comma_vs_cedilla", "see_same_identical",
             "Pairs that differ (ș vs ş)", "Byte-identical pairs",
             "Some models call every ș/ş pair different, even identical ones",
             "Accuracy on “Are these two strings the same sequence of Unicode characters?” · 6 pairs each",
             "Romanian Comma Below 4: See · Kaggle Benchmarks, 30 Sep 2026 · bars without a label are 100%",
             "chart-see.html")
    census_chart()


if __name__ == "__main__":
    main()
