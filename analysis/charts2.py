"""Round 2 charts for the post, in the same style as analysis/charts.py.

Reads results/round2_*.csv (written by analysis/round2.py) and the downloaded runs.
Usage:  uv run --no-project --with pandas --with numpy python analysis/charts2.py
        then: node post/render.mjs post/chart-*.html
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
from charts import C, POST, esc, page  # noqa: E402
import models as M  # noqa: E402
from round2 import boot_ci, ok_rows, rate_ci  # noqa: E402

FONT = 'font-family="system-ui, -apple-system, Segoe UI, sans-serif"'


def svg_open(W, H, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{esc(title)}">')


def header(title, sub, y=46):
    return (f'<text x="40" y="{y}" font-size="24" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>'
            f'<text x="40" y="{y + 28}" font-size="15" fill="{C["ink2"]}">{esc(sub)}</text>')


def write(file, title, parts):
    (POST / file).write_text(page(title, "".join(parts)), encoding="utf-8", newline="\n")
    print("wrote", file)


def axis(parts, X, y0, y1, ticks=(0, 25, 50, 75, 100)):
    for v in ticks:
        parts.append(f'<line x1="{X(v):.1f}" y1="{y0}" x2="{X(v):.1f}" y2="{y1}" stroke="{C["grid"]}" stroke-width="1"/>')
        parts.append(f'<text x="{X(v):.1f}" y="{y1 + 18}" font-size="13" fill="{C["muted"]}" text-anchor="middle">{v}%</text>')


def gap_chart(core_every, core_latest):
    """Hero: pooled share per probe, with one dot per model."""
    probes = [
        ("Writes ș/ț right from an English prompt", "Write",
         core_latest[core_latest.task == "write"], "item_id"),
        ("Spots a cedilla sentence when asked", "See: is there a cedilla in this sentence?",
         core_latest[(core_latest.task == "see") & (core_latest.note == "all cedilla")], "item_id"),
        ("Fixes it when told to correct the diacritics", "Fix",
         core_latest[(core_latest.task == "fix") & (core_latest.level == "L2_diacritics")], "base_id"),
        ("Fixes it when only told to proofread", "Fix",
         core_latest[(core_latest.task == "fix") & (core_latest.level == "L1_proofread")], "base_id"),
        ("Keeps ș/ț right when the input has ş/ţ", "Echo, cedilla input, 3 runs",
         core_every[(core_every.task == "echo") & (core_every.variant == "cedilla")], "base_id"),
    ]
    W, left, right, top, row_h = 1000, 360, 80, 132, 86
    H = top + row_h * len(probes) + 64
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    title = "They spot the cedilla and still copy it"
    p = [svg_open(W, H, title), header(title, "First round, the same 15 models on every row · bar = all answers, dot = one model")]
    axis(p, X, top - 18, top + row_h * len(probes) - 30)
    for i, (label, sub, df, cluster) in enumerate(probes):
        y = top + i * row_h
        pooled, lo, hi, n = rate_ci(df, cluster=cluster)
        color = C["s2"] if i == len(probes) - 1 else C["s1"]
        p.append(f'<text x="{left - 18}" y="{y + 6}" font-size="15.5" font-weight="600" fill="{C["ink"]}" text-anchor="end">{esc(label)}</text>')
        p.append(f'<text x="{left - 18}" y="{y + 26}" font-size="13" fill="{C["muted"]}" text-anchor="end">{esc(sub)} · n={n}</text>')
        w = X(pooled) - x0
        p.append(f'<rect x="{x0}" y="{y - 10}" width="{w:.1f}" height="22" rx="4" fill="{color}" opacity="0.22"/>')
        per = df.groupby("model")["pass"].mean() * 100
        for j, v in enumerate(sorted(per.values)):
            jitter = ((j % 5) - 2) * 3.2
            p.append(f'<circle cx="{X(v):.1f}" cy="{y + 1 + jitter:.1f}" r="4.2" fill="{color}" opacity="0.85"/>')
        p.append(f'<text x="{X(pooled) + 12:.1f}" y="{y + 30}" font-size="14" font-weight="600" fill="{C["ink2"]}">{pooled:.0f}%</text>')
    p.append(f'<text x="40" y="{H - 18}" font-size="13" fill="{C["muted"]}">Romanian Comma Below tasks 1, 4, 3 and 2 · Kaggle Benchmarks, 30 Sep – 1 Oct 2026</text>')
    p.append("</svg>")
    write("chart-gap.html", title, p)


def echo44_chart(t: pd.DataFrame, n_runs_note: str):
    """One row per model: cedilla input (dot + interval), ASCII input, cedilla + rule."""
    t = t.sort_values(["cedilla", "name"], ascending=[False, True]).reset_index(drop=True)
    W, left, right, top, row_h = 1000, 250, 70, 172, 27
    H = top + row_h * len(t) + 80
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    title = "Clean in, clean out. Cedilla in, cedilla out."
    sub = f"Share of answers that use only correct ș/ț letters · {len(t)} models · 22 prompts per input · {n_runs_note}"
    p = [svg_open(W, H, title), header(title, sub)]
    legend = [(C["s2"], "Typed with cedilla (ş ţ), bar = 95% interval"), (C["muted"], "Typed without diacritics"),
              (C["s3"], "Cedilla + one sentence in the system prompt")]
    lx = 40
    for color, label in legend:
        p.append(f'<circle cx="{lx + 6}" cy="110" r="6" fill="{color}"/>')
        p.append(f'<text x="{lx + 18}" y="115" font-size="14" fill="{C["ink2"]}">{esc(label)}</text>')
        lx += 34 + 7.0 * len(label)
    clean_min = t["clean"].min()
    p.append(f'<line x1="40" y1="138" x2="56" y2="138" stroke="{C["s1"]}" stroke-width="2"/>')
    p.append(f'<text x="64" y="143" font-size="14" fill="{C["ink2"]}">Typed correctly (ș ț): '
             f'{"100% for every model" if clean_min >= 99.95 else f"{clean_min:.0f}–100% across models"}</text>')
    axis(p, X, top - 16, top + row_h * len(t) - 8, ticks=(0, 25, 50, 75))
    p.append(f'<line x1="{X(100):.1f}" y1="{top - 16}" x2="{X(100):.1f}" y2="{top + row_h * len(t) - 8}" stroke="{C["s1"]}" stroke-width="2"/>')
    p.append(f'<text x="{X(100):.1f}" y="{top + row_h * len(t) + 10}" font-size="13" fill="{C["muted"]}" text-anchor="middle">100%</text>')
    for i, r in t.iterrows():
        y = top + i * row_h + 4
        p.append(f'<text x="{left - 14}" y="{y + 5}" font-size="14" fill="{C["ink"]}" text-anchor="end">{esc(r["name"])}</text>')
        if pd.notna(r.get("cedilla_lo")):
            p.append(f'<line x1="{X(r.cedilla_lo):.1f}" y1="{y}" x2="{X(r.cedilla_hi):.1f}" y2="{y}" stroke="{C["s2"]}" '
                     f'stroke-width="6" stroke-linecap="round" opacity="0.25"/>')
        if pd.notna(r.get("ascii")):
            p.append(f'<circle cx="{X(r.ascii):.1f}" cy="{y}" r="4.5" fill="{C["surface"]}" stroke="{C["muted"]}" stroke-width="2"/>')
        if pd.notna(r.get("cedilla+rule")):
            p.append(f'<circle cx="{X(r["cedilla+rule"]):.1f}" cy="{y}" r="5" fill="{C["s3"]}"/>')
        p.append(f'<circle cx="{X(r.cedilla):.1f}" cy="{y}" r="6" fill="{C["s2"]}" stroke="{C["surface"]}" stroke-width="2"/>')
        edge = min(r.cedilla, r.cedilla_lo) if pd.notna(r.get("cedilla_lo")) else r.cedilla
        p.append(f'<text x="{X(edge) - 10:.1f}" y="{y + 5}" font-size="12.5" fill="{C["ink2"]}" text-anchor="end">{r.cedilla:.0f}%</text>')
    p.append(f'<text x="40" y="{H - 22}" font-size="13" fill="{C["muted"]}">Romanian Comma Below 8: Echo, Four Inputs · '
             f'Kaggle Benchmarks, October 2026 · intervals resample the 22 prompts</text>')
    p.append("</svg>")
    write("chart-echo44.html", title, p)


def bars_chart(file, title, sub, groups, note, label_w=380):
    """groups: list of (group label, [(row label, pct, lo, hi, n, color)])."""
    rows = sum(len(g[1]) for g in groups)
    W, left, right, top, row_h, gap = 1000, label_w, 140, 120, 40, 34
    H = top + row_h * rows + gap * len(groups) + 50
    x0, x1 = left, W - right

    def X(v):
        return x0 + (x1 - x0) * v / 100

    p = [svg_open(W, H, title), header(title, sub)]
    y = top
    axis_top = top - 10
    for g_label, items in groups:
        p.append(f'<text x="40" y="{y + 4}" font-size="14" font-weight="600" fill="{C["muted"]}">{esc(g_label.upper())}</text>')
        y += 22
        for label, pct, lo, hi, n, color in items:
            p.append(f'<text x="{left - 16}" y="{y + 9}" font-size="14.5" fill="{C["ink"]}" text-anchor="end">{esc(label)}</text>')
            w = max(X(pct) - x0, 2)
            p.append(f'<rect x="{x0}" y="{y - 3}" width="{w:.1f}" height="18" rx="4" fill="{color}"/>')
            if pd.notna(lo) and pd.notna(hi) and hi > lo:
                p.append(f'<line x1="{X(lo):.1f}" y1="{y + 6}" x2="{X(hi):.1f}" y2="{y + 6}" stroke="{C["ink"]}" stroke-width="1.5" opacity="0.55"/>')
            p.append(f'<text x="{X(max(pct, hi if pd.notna(hi) else pct)) + 8:.1f}" y="{y + 11}" font-size="13" fill="{C["ink2"]}">{pct:.0f}%  (n={n})</text>')
            y += row_h
        y += gap - 22
    axis(p, X, axis_top, y - gap + 10)
    p.append(f'<text x="40" y="{H - 14}" font-size="13" fill="{C["muted"]}">{esc(note)}</text>')
    p.append("</svg>")
    write(file, title, p)


def lines_chart(t: pd.DataFrame):
    """Small multiples: cedilla pass by version inside product lines with >= 3 versions."""
    keep = [ln for ln, g in t.groupby("line") if len(g) >= 3]
    keep.sort(key=lambda ln: -len(t[t.line == ln]))
    if not keep:
        return
    cols = 2
    rows = (len(keep) + cols - 1) // cols
    W, cell_w, cell_h, top = 1000, 460, 230, 110
    H = top + rows * cell_h + 50
    title = "Claude dropped at version 5. Gemini Flash crept up."
    p = [svg_open(W, H, title), header(title, "Share of clean answers on cedilla input, by version · bars = 95% interval")]
    for k, ln in enumerate(keep):
        g = t[t.line == ln].sort_values("version").reset_index(drop=True)
        cx = 40 + (k % cols) * (cell_w + 40)
        cy = top + (k // cols) * cell_h
        p.append(f'<text x="{cx}" y="{cy + 14}" font-size="16" font-weight="600" fill="{C["ink"]}">{esc(ln)}</text>')
        px0, px1, py0, py1 = cx + 40, cx + cell_w - 20, cy + 40, cy + cell_h - 60

        def PX(i):
            return px0 + (px1 - px0) * (i / max(len(g) - 1, 1))

        def PY(v):
            return py1 - (py1 - py0) * v / 100

        for v in (0, 50, 100):
            p.append(f'<line x1="{px0}" y1="{PY(v):.1f}" x2="{px1}" y2="{PY(v):.1f}" stroke="{C["grid"]}"/>')
            p.append(f'<text x="{px0 - 8}" y="{PY(v) + 4:.1f}" font-size="12" fill="{C["muted"]}" text-anchor="end">{v}%</text>')
        pts = " ".join(f"{PX(i):.1f},{PY(v):.1f}" for i, v in enumerate(g.cedilla))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{C["s2"]}" stroke-width="2"/>')
        for i, r in g.iterrows():
            if pd.notna(r.cedilla_lo):
                p.append(f'<line x1="{PX(i):.1f}" y1="{PY(r.cedilla_lo):.1f}" x2="{PX(i):.1f}" y2="{PY(r.cedilla_hi):.1f}" '
                         f'stroke="{C["s2"]}" stroke-width="5" opacity="0.25" stroke-linecap="round"/>')
            p.append(f'<circle cx="{PX(i):.1f}" cy="{PY(r.cedilla):.1f}" r="5" fill="{C["s2"]}"/>')
            short = r["name"].replace("Claude ", "").replace("Gemini ", "").replace(" Flash", "").replace("GPT-", "")
            p.append(f'<text x="{PX(i):.1f}" y="{py1 + 20}" font-size="12" fill="{C["ink2"]}" text-anchor="middle">{esc(short)}</text>')
            p.append(f'<text x="{PX(i):.1f}" y="{PY(r.cedilla) - 10:.1f}" font-size="12" fill="{C["ink2"]}" text-anchor="middle">{r.cedilla:.0f}</text>')
    p.append(f'<text x="40" y="{H - 16}" font-size="13" fill="{C["muted"]}">Romanian Comma Below 8: Echo, Four Inputs · Kaggle Benchmarks, October 2026</text>')
    p.append("</svg>")
    write("chart-lines.html", title, p)


def main():
    every = ok_rows(load(all_runs=True))
    latest = ok_rows(load())
    core = set(M.CORE)
    gap_chart(every[every.model.isin(core)], latest[latest.model.isin(core)])

    t = pd.read_csv("results/round2_echo4_models.csv")
    t = t[~t.model.isin({"grok-4.6", "grok-4.5-0708"})]
    runs = t["runs"] if "runs" in t else pd.Series([1])
    echo44_chart(t, f"{int(runs.min())}–{int(runs.max())} runs per model")
    lines_chart(t)

    e4 = every[every.task == "echo4"]
    lk = every[every.task == "lookalike"]
    groups = []
    ro = [("Typed without diacritics (Brasov)", e4[e4.variant == "ascii"], C["muted"]),
          ("Typed with the cedilla (Braşov)", e4[e4.variant == "cedilla"], C["s2"])]
    groups.append(("Romanian, 22 prompts", [(lab, *rate_ci(df), col) for lab, df, col in ro if len(df)]))
    if len(lk):
        en = [("Mojibake in the names (ZÃ¼rich)", lk[lk.variant == "mojibake"], C["muted"]),
              ("Cyrillic look-alikes in the names (Zürісһ)", lk[lk.variant == "cyrillic-names"], C["muted"]),
              ("Cyrillic look-alikes in every word", lk[lk.variant == "cyrillic-all"], C["muted"])]
        groups.append(("English, 12 prompts", [(lab, *rate_ci(df), col) for lab, df, col in en if len(df)]))
    bars_chart("chart-lookright.html", "What gets repaired and what gets copied",
               "Share of answers that came back clean, by how the input was damaged · bars = 95% interval",
               groups, "Romanian Comma Below 8 and 11 · Kaggle Benchmarks, October 2026", label_w=430)

    k9 = every[every.task == "contagion"]
    tu = every[every.task == "turns"]
    spread = []
    if len(k9):
        rows = []
        for cond, lab in (("clean-0", "All four documents clean"), ("clean-1", "Target clean, 1 other in cedilla"),
                          ("clean-3", "Target clean, 3 others in cedilla")):
            rows.append((lab, *rate_ci(k9[k9.cond == cond], cluster="set_id"), C["s1"] if cond == "clean-0" else C["s2"]))
        for cond, lab in (("cedilla-0", "Target in cedilla, others clean"), ("cedilla-3", "All four in cedilla")):
            rows.append((lab, *rate_ci(k9[k9.cond == cond], cluster="set_id"), C["muted"]))
        spread.append(("Answer about one of four documents", rows))
    if len(tu):
        rows = [(lab, *rate_ci(tu[tu.cond == cond], cluster="pair_id"), col) for cond, lab, col in
                (("clean>clean", "Second text clean, first clean", C["s1"]),
                 ("cedilla>clean", "Second text clean, first in cedilla", C["s2"]),
                 ("clean>cedilla", "Second text in cedilla, first clean", C["muted"]))]
        spread.append(("Second summary in the same chat", rows))
    if spread:
        bars_chart("chart-spread.html", "Does the cedilla spread to text that was typed correctly?",
                   "Share of clean answers · bars = 95% interval", spread,
                   "Romanian Comma Below 9: Contagion and 12: Turns · Kaggle Benchmarks, October 2026", label_w=400)

    tr = every[every.task == "turkish"]
    if len(tr):
        hand = pd.read_csv("results/round2_turkish_replies.csv")
        hand["pass"] = hand.outcome == "correct"
        rows_tr = [(lab, *rate_ci(hand[hand.rule == r]), col) for r, lab, col in
                   (("none", "No rule", C["s1"]), ("rule", "“Never write ş or ţ” (task 7's rule)", C["s2"]),
                    ("scoped", "The same rule, for Romanian only", C["s3"]))]
        rows_ro = [(lab, *rate_ci(e), col) for lab, e, col in
                   (("No rule (task 8)", e4[e4.variant == "cedilla"], C["s1"]),
                    ("“Never write ş or ţ”", e4[e4.variant == "cedilla+rule"], C["s2"]),
                    ("The same rule, for Romanian only", tr[(tr.lang == "ro") & (tr.rule == "scoped")], C["s3"]))]
        bars_chart("chart-fix.html", "One sentence fixes Romanian. Scoped, it spares most of the Turkish.",
                   "Share of correct answers · bars = 95% interval",
                   [("Romanian, typed with cedilla", rows_ro),
                    ("Turkish, where ş is correct: correct replies", rows_tr)],
                   "Romanian Comma Below 8 and 10 · Kaggle Benchmarks, October 2026", label_w=400)


if __name__ == "__main__":
    main()
