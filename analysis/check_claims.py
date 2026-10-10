"""Recompute the numbers the post quotes, and check the post against them.

  --values   write results/post_values.json (the {{NAME}} numbers that post/finalize3.py fills in)
  (default)  check post/post-v3-dev.md: every number in it must be a recomputed value, and every quote
             must be in the data

A few numbers need the run traces (results/raw/**/*.run.json: DeepSeek-R1's reasoning and the cost),
which stay on Kaggle and are not in the repo. Without them those values are kept from the committed
results/post_values.json, and the script says which.

Usage:  uv run --no-project --with pandas --with numpy python analysis/check_claims.py [--values]
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
import models as M  # noqa: E402
from items import ECHO, ECHO_RAG, to_cedilla  # noqa: E402
from round2 import ok_rows  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_R1 = {"grok-4.6", "grok-4.5-0708", "gpt-oss-120b"}
VALUES = ROOT / "results" / "post_values.json"


def pct(x) -> int:
    return int(round(100 * float(x)))


def holm(st: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """The version steps that survive a Holm-Bonferroni correction over all of them, smallest p first."""
    m, keep = len(st), []
    for i, r in enumerate(st.sort_values("p").itertuples()):
        if r.p > alpha / (m - i):
            break
        keep.append(r.Index)
    return st.loc[keep]


def have_traces() -> bool:
    """The run traces (*.run.json) stay on Kaggle; a clone of the repo has only the answers (*.jsonl)."""
    return next((ROOT / "results" / "raw").glob("*/*/*/*/*.run.json"), None) is not None


def keep_committed(v: dict, keys: tuple[str, ...], kept: list[str]):
    """Without the run traces, take these values from the committed post_values.json."""
    old = json.loads(VALUES.read_text(encoding="utf-8")) if VALUES.exists() else {}
    for k in keys:
        if k in old:
            v[k] = old[k]
            kept.append(k)


def values() -> dict:
    raw_every, raw_latest = load(all_runs=True), load()  # raw: as the tasks scored them on Kaggle
    every = ok_rows(raw_every)
    latest = ok_rows(raw_latest)
    kept: list[str] = []
    r1e = every[~every.model.isin(EXCLUDE_R1)]
    r1l = latest[~latest.model.isin(EXCLUDE_R1)]
    v: dict[str, object] = {}

    # Round 1 (15 models)
    echo = r1e[(r1e.task == "echo")]
    ce = echo[echo.variant == "cedilla"]
    v["R1_WRITE"] = pct(r1l[r1l.task == "write"]["pass"].mean())
    v["R1_SEE_ALL"] = pct(r1l[(r1l.task == "see") & (r1l.note == "all cedilla")]["pass"].mean())
    v["R1_FIX_L2"] = pct(r1l[(r1l.task == "fix") & (r1l.level == "L2_diacritics")]["pass"].mean())
    v["R1_ECHO_CED"] = pct(ce["pass"].mean())
    v["R1_ECHO_CLEAN"] = pct(echo[echo.variant == "clean"]["pass"].mean())
    n_words = sum(len(x) for x in ce.cedilla_words)
    n_copied = sum(len(x) for x in ce.cedilla_words_copied)
    v["R1_COPIED"] = pct(n_copied / n_words)
    r1_values(r1l, v)
    see_final_values(r1l, v)
    v["GROK_ECHO"] = pct(ce[ce.model == "grok-4.20-0309-reasoning"]["pass"].mean())

    # Round 2, task 8
    e4 = every[(every.task == "echo4")]
    if len(e4):
        served = sorted(set(e4.model))
        v["N_MODELS"] = len(served)
        v["N_NEW"] = len([m for m in served if m not in M.CORE])
        for var, key in (("clean", "E4_CLEAN"), ("cedilla", "E4_CED"), ("ascii", "E4_ASCII"), ("cedilla+rule", "E4_RULE")):
            v[key] = pct(e4[e4.variant == var]["pass"].mean())
        c4 = e4[e4.variant == "cedilla"]
        for kind, key in (("reply", "E4_REPLY"), ("summary", "E4_SUMMARY"), ("rag", "E4_RAG")):
            v[key] = pct(c4[c4.kind == kind]["pass"].mean())
        t = pd.read_csv(ROOT / "results" / "round2_echo4_models.csv")
        t = t[t.model.isin(served)]
        lo, hi = t.loc[t.cedilla.idxmin()], t.loc[t.cedilla.idxmax()]
        v["E4_MIN"], v["E4_MIN_NAME"] = f"{lo.cedilla:.0f}", lo["name"]
        v["E4_MAX"], v["E4_MAX_NAME"] = f"{hi.cedilla:.0f}", hi["name"]
        v["N_WHOLE"] = int((t.whole_answer_share >= 50).sum())
        low = t[t["cedilla+rule"] < 80].sort_values("cedilla+rule")
        names = [f"{r['name']} ({r['cedilla+rule']:.0f} %)" for _, r in low.iterrows()]
        v["RULE_LOW"] = (", ".join(names[:-1]) + " and " + names[-1]) if len(names) > 1 else (names[0] if names else "no model")
        v["N_WITH_FAILS"] = int((t.fails > 0).sum())
        oss = e4[(e4.model == "gpt-oss-120b") & (e4.variant == "clean")]
        if len(oss):
            v["OSS_CLEAN_CED"] = pct((oss.cedilla > 0).mean())
        both = every[every.task.isin(["echo", "echo4"]) & every.model.isin(["gpt-oss-20b", "gpt-oss-120b"])
                     & (every.variant == "clean")]
        if len(both):
            v["OSS_CLEAN_K"], v["OSS_CLEAN_N"] = int((both.cedilla > 0).sum()), len(both)
        # best models (ties at the top) and run-to-run spread on the same prompts
        top = t[t.cedilla >= t.cedilla.max() - 0.01].sort_values("name")
        v["TOP_NAMES"] = ", ".join(top["name"])
        v["TOP_SCORE"] = f"{t.cedilla.max():.0f}"
        runs = every[every.task.isin(["echo", "echo4"]) & (every.variant == "cedilla") & (every.model != "gpt-oss-120b")]
        rr = runs.groupby(["model", "task", "run_id"])["pass"].mean().reset_index()
        sp = rr.groupby("model")["pass"].agg(["min", "max", "count"])
        sp = sp[sp["count"] >= 2]
        rng = 100 * (sp["max"] - sp["min"])
        v["RUN_SPREAD_MED"], v["RUN_SPREAD_MAX"], v["RUN_SPREAD_N"] = f"{rng.median():.0f}", f"{rng.max():.0f}", len(sp)
        # the same on round one's identical task 2 runs only (3 per model), the base of FLIP_R1: the
        # numbers above mix models with 2 runs and models with 4, and a range grows with the number of runs
        r1 = every[(every.task == "echo") & (every.variant == "cedilla")].groupby(["model", "run_id"])["pass"].mean()
        sp1 = r1.groupby("model").agg(["min", "max", "count"])
        rng1 = 100 * (sp1["max"] - sp1["min"])[sp1["count"] >= 2]
        v["RUN_SPREAD_R1_MED"], v["RUN_SPREAD_R1_MAX"] = int(round(rng1.median())), int(round(rng1.max()))
        q = e4[(e4.model == "qwen3-next-80b-a3b-thinking") & (e4.variant == "cedilla")]
        v["QWEN_T_N"] = len(q)
        # Kaggle's task 8 score counts an empty answer (the token cap ran out while thinking) as a failure
        qk = raw_latest[(raw_latest.task == "echo4") & (raw_latest.model == "qwen3-next-80b-a3b-thinking")
                        & (raw_latest.variant == "cedilla") & raw_latest["error"].isna()]
        if len(qk):
            v["QWEN_T_KAGGLE"] = pct(qk["pass"].mean())
        r2small = every[every.task.isin(["contagion", "turkish", "lookalike", "turns"])]
        v["N_R2_SMALL"] = r2small.model.nunique()
        # where the cedilla words in task 8 answers come from: exact copies, inflected or joined forms, new words
        import os
        from items import ECHO as _ECHO, ECHO_RAG as _RAG, to_cedilla as _ced
        from scoring import words as _words
        src = {i: _ced(t) for i, _, t in _ECHO}
        exact = infl = new = 0
        for r in e4[e4.variant == "cedilla"].itertuples():
            b = r.base_id
            inp = {w.casefold() for w in _words(src[_RAG[int(b[1:]) - 1][0]] if b.startswith("Q") else src[b])}
            for w in r.cedilla_words:
                wc = w.casefold()
                if wc in inp:
                    exact += 1
                elif all(p in inp for p in wc.split("-")) or any(len(os.path.commonprefix([wc, x])) >= 5 for x in inp):
                    infl += 1
                else:
                    new += 1
        tot = exact + infl + new
        v["E4_COPY_EXACT"], v["E4_COPY_INFL"], v["E4_COPY_NEW"] = pct(exact / tot), pct(infl / tot), pct(new / tot)
        v["E4_CED_WORDS"] = tot
        words_c = e4[e4.variant == "cedilla"]
        words_a = e4[e4.variant == "ascii"]
        v["E4_WORD_CED"] = f"{100 * words_c.st_cedilla.sum() / words_c.st_total.sum():.0f}"
        v["E4_WORD_ASCII"] = f"{100 * words_a.st_ascii.sum() / words_a.st_total.sum():.1f}"
        # per-model values used in the findings: every run of the same 22 prompts (task 8, plus tasks 2 and 7
        # for the round one models), the basis of the version test, the upgrades chart and the results table
        by = t.set_index("model")[["cedilla"]]
        named = {"OPUS_45": "claude-opus-4-5-20251101", "OPUS_48": "claude-opus-4-8-default", "OPUS_5": "claude-opus-5-default",
                 "OPUS_55": "claude-opus-5-5-default", "SONNET_45": "claude-sonnet-4-5-20250929",
                 "SONNET_46": "claude-sonnet-4-6-default", "SONNET_5": "claude-sonnet-5-default",
                 "SONNET_55": "claude-sonnet-5-5-default", "SOL_56": "gpt-5.6-sol", "SOL_6": "gpt-6-sol",
                 "SOL_61": "gpt-6.1-sol", "LUNA_56": "gpt-5.6-luna", "LUNA_6": "gpt-6-luna",
                 "FLASH_25": "gemini-2.5-flash", "FLASH_37": "gemini-3.7-flash", "FLASH_38": "gemini-3.8-flash",
                 "GROK_R": "grok-4.20-0309-reasoning", "GROK_NR": "grok-4.20-0309-non-reasoning"}
        for key, slug in named.items():
            if slug in by.index:
                v[f"V_{key}"] = f"{by.loc[slug, 'cedilla']:.0f}"
        steps_f = ROOT / "results" / "round2_version_steps.csv"
        if steps_f.exists():
            st_all = pd.read_csv(steps_f)
            st = st_all[st_all.kind == "version"]
            v["N_STEPS"] = len(st)
            v["N_STEPS_SIG"] = int((st.p < 0.05).sum())
            v["N_STEPS_DOWN"] = int(((st.p < 0.05) & (st.change < 0)).sum())
            v["N_STEPS_UP"] = int(((st.p < 0.05) & (st.change > 0)).sum())
            # Holm-Bonferroni over the version steps
            surv = [f"{r.older} → {r.newer.replace('Claude ', '').replace('Gemini ', '')} ({r.change:+.0f} points)"
                    for r in holm(st).itertuples()]
            v["STEPS_HOLM"] = (", ".join(surv[:-1]) + " and " + surv[-1]) if len(surv) > 1 else (surv[0] if surv else "none")
            v["N_STEPS_HOLM"] = len(surv)
            for r in st_all.itertuples():
                key = (r.older + "_" + r.newer).upper().replace("CLAUDE ", "").replace("GEMINI ", "").replace(" ", "").replace(".", "").replace("-", "")
                v[f"STEP_{key}"] = f"{r.change:+.0f} points (p = {r.p:.3f})".replace("p = 0.000", "p < 0.001")
        tested = sorted(set(every.model) - {"grok-4.6", "grok-4.5-0708"})  # every model with an answer in any task
        v["N_MODELS_ALL"] = len(tested)
        missing = [M.name(m) for m in tested if m not in served]
        v["E4_MISSING_NOTE"] = (f" {' and '.join(missing)}'s runs of the four-way test failed, so that test has "
                                f"{len(served)} models." if missing else "")
        labs = {}
        for m in sorted(tested, key=lambda m: (M.line(m), M.version(m), M.name(m))):  # Opus 5 before Opus 5.5
            labs.setdefault(M.lab(m), []).append(M.name(m))
        order = ["Anthropic", "Google", "OpenAI", "xAI", "DeepSeek", "Alibaba", "Zhipu"]
        v["MODELS_LINE"] = " ".join(f"**{lab}:** {', '.join(labs[lab])}." for lab in order if lab in labs)

    # results table: the 15 core models, every task they ran
    if len(e4):
        rows = []
        for m in M.CORE:
            r1m = r1l[r1l.model == m]
            ech = pd.concat([every[(every.model == m) & (every.task == "echo") & (every.variant == "cedilla")],
                             e4[(e4.model == m) & (e4.variant == "cedilla")]])
            e4m = e4[e4.model == m]
            rule = pd.concat([every[(every.model == m) & (every.task == "rule")], e4m[e4m.variant == "cedilla+rule"]])

            def p(df, col="pass"):
                return "–" if df.empty else f"{100 * df[col].astype(float).mean():.0f}"

            rows.append((ech["pass"].mean() if len(ech) else -1, [
                M.name(m), p(r1m[r1m.task == "write"]), p(ech), p(e4m[e4m.variant == "ascii"]),
                p(rule), p(r1m[r1m.task == "fix"]), p(r1m[r1m.task == "see"]),
                p(r1m[r1m.task == "restore"]), p(r1m[r1m.task == "code"], "score")]))
        rows.sort(key=lambda t: -t[0])
        head = ("| Model | Write | Echo: cedilla | Echo: no diacritics | Echo + rule | Fix | See | Restore | Code |\n"
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        v["TABLE"] = head + "\n" + "\n".join("| " + " | ".join(r) + " |" for _, r in rows)

    tr = every[every.task == "turkish"]
    if len(tr):
        t = tr[tr.lang == "tr"]
        v["N_TR_MODELS"] = t.model.nunique()
        v["TR_NONE"] = pct(t[t.rule == "none"]["pass"].mean())
        # one hand-checked outcome per Turkish reply (written by round2.py)
        o = pd.read_csv(ROOT / "results" / "round2_turkish_replies.csv")
        for rule, key in (("none", "NONE"), ("rule", "RULE"), ("scoped", "SCOPED")):
            x = o[o.rule == rule]
            share = x.outcome.value_counts(normalize=True)
            v[f"TR_{key}"] = pct(share.get("correct", 0.0))
            v[f"TR_{key}_RO"] = pct(share.get("romanian", 0.0))
            v[f"TR_{key}_NOS"] = pct(share.get("no_s", 0.0))
            v[f"TR_{key}_COMMA"] = pct(share.get("turkish_with_comma", 0.0))
            v[f"N_TR_{key}_BROKE"] = int(x.groupby("model").outcome.apply(lambda s: (s != "correct").any()).sum())
        v["N_TR_BROKE"] = v["N_TR_RULE_BROKE"]
        v["N_TR_SCOPED_BROKE"] = v["N_TR_SCOPED_BROKE"]
        # the same replies as task 10 scored them on Kaggle: its name list has the places, not the dishes and
        # villages the word-level reading above also treats as names, so 4 replies fail there and count here
        tk = raw_every[(raw_every.task == "turkish") & (raw_every.lang == "tr") & raw_every["error"].isna()]
        v["TR_RULE_KAGGLE"] = f"{100 * tk[tk.rule == 'rule']['pass'].mean():.1f}"
        v["TR_SCOPED_KAGGLE"] = f"{100 * tk[tk.rule == 'scoped']['pass'].mean():.1f}"
        ro = tr[tr.lang == "ro"]
        v["RO_RULE"] = pct(ro[ro.rule == "rule"]["pass"].mean())
        v["RO_SCOPED"] = pct(ro[ro.rule == "scoped"]["pass"].mean())

    lk = every[every.task == "lookalike"]
    if len(lk):
        v["N_LK_MODELS"] = lk.model.nunique()
        for var, key in (("clean", "LK_CLEAN"), ("cyrillic-all", "LK_CYR_ALL"), ("cyrillic-names", "LK_CYR_NAMES"),
                         ("mojibake", "LK_MOJI")):
            v[key] = pct(lk[lk.variant == var]["pass"].mean())
        mo = lk[lk.variant == "mojibake"]
        v["LK_MOJI_RAG"] = pct(mo[mo.kind == "rag"]["pass"].mean())
        v["LK_MOJI_SUM"] = pct(mo[mo.kind == "summary"]["pass"].mean())
        cy = lk[lk.variant.isin(["cyrillic-all", "cyrillic-names"])]
        v["LK_CYR_COPIED"] = pct(1 - cy["pass"].mean())
        v["LK_MOJI_COPIED_RAG"] = pct(1 - mo[mo.kind == "rag"]["pass"].mean())

    ds, _ = deepseek_reasoning()
    if len(ds):
        nr, ru = ds[~ds.rule], ds[ds.rule]
        v["DS_NR_N"], v["DS_NR_TALK"], v["DS_NR_COPIED"] = len(nr), int(nr.talks.sum()), int(nr.copied.sum())
        v["DS_RU_N"], v["DS_RU_TALK"] = len(ru), int(ru.talks.sum())
        v["DS_RU_TALK_COPIED"] = int((ru.talks & ru.copied).sum())
    elif not have_traces():
        keep_committed(v, ("DS_NR_N", "DS_NR_TALK", "DS_NR_COPIED", "DS_RU_N", "DS_RU_TALK", "DS_RU_TALK_COPIED"), kept)
    if len(e4):
        c8 = e4[e4.variant == "cedilla"]
        says = c8.response.fillna("").str.contains(r"sedil|cedil|diacritic|ortograf|virgul|comma below|encoding", case=False)
        v["N_CED_ANSWERS"], v["N_CED_SAY"] = len(c8), int(says.sum())
        v["N_CED_FIXED"], v["N_CED_COPIED"] = int(c8["pass"].astype(bool).sum()), int((~c8["pass"].astype(bool)).sum())
    from round2 import spearman as _sp
    see_m = r1l[r1l.task == "see"].groupby("model")["pass"].mean()
    ech_m = ce.groupby("model")["pass"].mean()
    jj = pd.concat([see_m.rename("see"), ech_m.rename("echo")], axis=1).dropna()
    v["SPOT_COPY_RHO"] = f"{_sp(jj.see, jj.echo):.2f}"

    v["PREDICTIONS"], counts, v["PRED_NOTE"] = predictions(every)
    v.update({"PRED_" + k.upper().replace(" ", "_"): n for k, n in counts.items()})
    third_version_values(every, v)

    # cost of everything downloaded (all tasks, pilots, reruns)
    import costs  # noqa: E402
    if have_traces():
        total = 0.0
        for f in (ROOT / "results" / "raw").glob("*/*/*/*/*.run.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            for m in costs.requests(d):
                total += (int(m.get("inputTokensCostNanodollars", 0) or 0) + int(m.get("outputTokensCostNanodollars", 0) or 0)) / 1e9
        v["COST"] = f"{total:.2f}"
    else:
        keep_committed(v, ("COST",), kept)
    if kept:
        print("no run traces (results/raw/**/*.run.json, not in the repo): kept from the committed "
              f"results/post_values.json: {', '.join(kept)}")

    import extras  # noqa: E402  (analysis/extras.py: values for the post's newer paragraphs)
    extras.add(v, every, latest)
    return v


def third_version_values(every: pd.DataFrame, v: dict):
    """Numbers new in the third version of the post: own words, the fixes, run-to-run flips, word pairs."""
    import own_words as OW  # noqa: E402
    from fix_check import fix_naive, fix_romanian, is_hos, romanian_base, turkish_base  # noqa: E402

    # the model's own new words follow the copied cedilla (tasks 2 and 8, answers to cedilla input)
    a = OW.answers(every)
    s = OW.summary(a)
    k, n = s["all_or_none"]
    v["ALLNONE_PCT"] = pct(k / n)
    for g, key in (("all", "OWN_ALL"), ("some", "OWN_SOME"), ("none", "OWN_NONE")):
        c, t = s[g][0], s[g][1]
        share = 100 * c / t if t else float("nan")  # one decimal under 10 %, as the keyboard chart prints it
        v[f"{key}_K"], v[f"{key}_N"] = c, t
        v[f"{key}_PCT"] = ("n/a" if not t else f"{share:.1f}" if 0 < share < 10 else pct(c / t))
    haiku = s.get("within", {}).get("claude-haiku-4-5-20251001")
    if haiku:
        v["HAIKU_ALL"], v["HAIKU_SOME"] = f"{haiku[0]} of {haiku[1]}", f"{haiku[2]} of {haiku[3]}"

    # fixes in code, measured on the models' answers (analysis/fix_check.py prints the same numbers)
    tr = every[every.task == "turkish"]
    if len(tr):
        # the bot's own correct Turkish replies (no rule), the same base as chart-fixes
        tt = turkish_base(every)
        tr_text = tt.response.fillna("").map(lambda r: unicodedata.normalize("NFC", r))
        v["FIX_TR_N"] = len(tt)
        v["FIX_NAIVE_ALTERED"] = int(sum(fix_naive(r) != r for r in tr_text))
        v["FIX_TR_ALTERED"] = int(sum(fix_romanian(r) != r for r in tr_text))
        # of those, short greetings with "hoş" (Hoş geldiniz) and no ı ğ ç ö ü to mark them as Turkish
        v["FIX_TR_HOS"] = int(sum(fix_romanian(r) != r and is_hos(r) for r in tr_text))
    with_ced = romanian_base(every)
    v["FIX_RO_N"] = len(with_ced)
    v["FIX_RO_LEFT"] = int(sum(any(c in fix_romanian(r) for c in "şŞţŢ") for r in with_ced.response.fillna("")))

    # run-to-run flips: model x prompt cells whose identical reruns disagree (clean in one run, not in another)
    for task, key in (("echo", "FLIP_R1"), ("echo4", "FLIP_R2")):
        e = every[(every.task == task) & (every.variant == "cedilla")]
        g = e.groupby(["model", "item_id"])["pass"].agg(["min", "max", "count"])
        g = g[g["count"] >= 2]
        if len(g):
            v[key] = pct((g["min"] != g["max"]).mean())
            v[key + "_CELLS"] = len(g)

    # the 12 word pairs of task 4, which the human test reuses
    see = every[(every.task == "see") & (every.kind == "same") & ~every.note.fillna("").str.startswith("control")]
    see = see[~see.model.isin(EXCLUDE_R1)]
    if len(see):
        v["SEE_PAIRS_PCT"] = pct(see["pass"].mean())
        v["SEE_DIFF_K"] = int(see[see.note == "comma vs cedilla"]["pass"].sum())
        v["SEE_DIFF_N"] = int((see.note == "comma vs cedilla").sum())
        v["SEE_SAME_PCT"] = pct(see[see.note != "comma vs cedilla"]["pass"].mean())

    # the human test on the same word pairs (totals only; the codes stay local)
    hs = ROOT / "results" / "human_summary.json"
    if hs.exists():
        h = json.loads(hs.read_text(encoding="utf-8"))
        v["HUMAN_N"], v["HUMAN_SD"], v["HUMAN_WR"] = h["n"], h["sd_pct"], h["wr_pct"]
        v["HUMAN_SD_LO"], v["HUMAN_SD_HI"] = h["sd_ci"]
        v["HUMAN_AUTHOR_SD"] = h["author_sd"]
        # version 1 of the page (the n above); 6 of its 12 pairs are identical, so all "same" scores exactly 50 %
        assert v["HUMAN_SD"] == 50, "the post says the people scored exactly what answering 'same' every time gets"

    # reruns: each model's clean share on cedilla input, run by run (tasks 2 and 8, the same prompts)
    runs = every[every.task.isin(["echo", "echo4"]) & (every.variant == "cedilla")]
    per_run = runs.groupby(["model", "task", "run_id"])["pass"].mean() * 100
    for m, key in (("claude-opus-4-8-default", "OPUS48"), ("claude-opus-5-default", "OPUS5")):
        r = per_run.loc[m] if m in per_run.index.get_level_values(0) else None
        if r is not None and len(r):
            lo, hi = r.min(), r.max()
            v[f"{key}_RUNS_N"] = len(r)
            which = {2: "both", 3: "all three", 4: "all four", 5: "all five"}.get(len(r), f"all {len(r)}")
            v[f"{key}_RUNS"] = (f"{lo:.0f} % in {which} of its runs" if round(lo) == round(hi) else
                                f"between {lo:.0f} and {hi:.0f} % in {which} of its runs")
    # a fresh run of the same kind of prompts: task 13's cedilla control, per Claude version
    w13 = every[(every.task == "wrong") & (every.variant == "cedilla")]
    for m, key in (("claude-sonnet-4-6-default", "T13_SONNET46"), ("claude-sonnet-5-default", "T13_SONNET5"),
                   ("claude-opus-4-8-default", "T13_OPUS48"), ("claude-opus-5-default", "T13_OPUS5")):
        d = w13[w13.model == m]
        if len(d):
            v[key] = pct(d["pass"].mean())
    if all(k in v for k in ("T13_SONNET46", "T13_SONNET5", "T13_OPUS48", "T13_OPUS5")):
        assert v["T13_SONNET46"] > v["T13_SONNET5"] and v["T13_OPUS48"] > v["T13_OPUS5"],             "the post says the fresh run put both pairs of versions in the same order"
    # the own-word replication in task 13 (pre-registered prediction 5)
    w = every[every.task == "wrong"]
    if len(w) and w.model.nunique() >= 10:
        import task13 as T13  # noqa: E402
        w13p = T13.prepare(w)
        g13 = T13.own_words(w13p, "cedilla")
        v["T13_OWN_ALL_K"], v["T13_OWN_ALL_N"] = g13["all"][2], g13["all"][1]
        v["T13_OWN_SOME_K"], v["T13_OWN_SOME_N"] = g13["some"][2], g13["some"][1]
        v["T13_DOT_REPLACED"] = f"{100 - T13.paired(w13p, 'dot', 'cedilla')['a']:.0f}"
    # models with enough new words in both groups to compare inside one model
    within = s.get("within", {})
    both = [(m, x) for m, x in within.items() if x[1] >= 10 and x[3] >= 10]
    parts = [f"{M.name(m)} {'went ' if k == 0 else ''}{x[0]} of {x[1]} against {x[2]} of {x[3]}"
             for k, (m, x) in enumerate(sorted(both, key=lambda t: -t[1][1]))]
    v["WITHIN_TEXT"] = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + ", and " + parts[-1]
    v["WITHIN_N"] = {1: "one model", 2: "two models", 3: "three models"}.get(len(both), f"{len(both)} models")
    assert all(x[0] / x[1] > x[2] / x[3] for _, x in both), "the post says the gap holds inside each of these models"
    # tasks 9-12 ran on different numbers of models
    n9_12 = [every[every.task == t].model.nunique() for t in ("contagion", "turkish", "lookalike", "turns")]
    v["N_R2_MIN"], v["N_R2_MAX"] = min(n9_12), max(n9_12)
    # silence across every task with cedilla input and no rule: the answer never mentions the letters
    talk = r"sedil|cedil|diacritic|ortograf|virgul|comma below|encoding"
    ced_in = every[((every.task == "echo") & (every.variant == "cedilla"))
                   | ((every.task == "echo4") & (every.variant == "cedilla"))
                   | ((every.task == "contagion") & (every.cond != "clean-0"))
                   | ((every.task == "turns") & (every.cond != "clean>clean"))
                   | ((every.task == "wrong") & (every.variant == "cedilla"))]
    v["N_CED_ALL"] = f"{len(ced_in):,}"
    v["N_CED_ALL_SAY"] = int(ced_in.response.fillna("").str.contains(talk, case=False).sum())
    v["N_CED_ALL_TASKS"] = ced_in.task.nunique()
    assert v["N_CED_ALL_SAY"] == 0, "the post says no answer to cedilla input mentioned the letters"
    # task 13's own predictions
    if "PREDICTIONS" in v:
        t13 = [l for l in v["PREDICTIONS"].splitlines() if l.startswith("| 13 |")]
        held = sum(l.rstrip().endswith("| held |") for l in t13)
        v["T13_PRED_PHRASE"] = (f"all {len(t13)} of its predictions held" if held == len(t13)
                                else f"{held} of its {len(t13)} predictions held")

    # phrasing that depends on the numbers, so the text stays true when they change
    v["PRED_UNCLEAR"] = v.get("PRED_MIXED", 0) + v.get("PRED_INCONCLUSIVE", 0)
    if "N_CED_ANSWERS" in v:
        v["N_CED_ANSWERS_TXT"] = f"{v['N_CED_ANSWERS']:,}"
    if "FIX_TR_N" in v:
        v["FIX_NAIVE_PHRASE"] = (f"all {v['FIX_TR_N']}" if v["FIX_NAIVE_ALTERED"] == v["FIX_TR_N"]
                                 else f"{v['FIX_NAIVE_ALTERED']} of the {v['FIX_TR_N']}")
        assert v["FIX_RO_LEFT"] == 0, "the post says the fix cleaned every Romanian answer"
    assert v.get("N_CED_SAY", 0) == 0, "the post says no answer mentioned the letters"
    assert v.get("R1_SEE_ALL") == 100, "the post says every model found the cedilla in every cedilla sentence"
    assert 60 <= v.get("SEE_SAME_PCT", 0) <= 72, "the post says models called identical pairs different a third of the time"
    holm = str(v.get("STEPS_HOLM", ""))
    assert "Opus 4.8" in holm and "Sonnet 4.6" in holm, "the post says both drops survive the correction"

    # contagion (task 9) and turns (task 12)
    k9 = every[every.task == "contagion"]
    if len(k9):
        v["N_K9"] = k9.model.nunique()
        per9 = k9.pivot_table(index="model", columns="cond", values="pass", aggfunc="mean") * 100
        d9 = per9["cedilla-0"] - per9["cedilla-3"]
        v["K9_LOWER"], v["K9_HIGHER"] = int((d9 > 0).sum()), int((d9 < 0).sum())
        movers = per9[(per9["clean-1"] < per9["clean-0"]) | (per9["clean-3"] < per9["clean-0"])].index
        v["K9_CLEAN_MOVERS"] = " and ".join(M.name(m) for m in movers) if len(movers) <= 2 else (
            ", ".join(M.name(m) for m in movers[:-1]) + " and " + M.name(movers[-1]))
        assert v["K9_HIGHER"] == 0, "the post says no model moved the other way"
        assert 1 <= len(movers) <= 3, "the post says only a few models slipped around a clean document"
        for cond, key in (("clean-0", "K9_CLEAN0"), ("clean-1", "K9_CLEAN1"), ("clean-3", "K9_CLEAN3"),
                          ("cedilla-0", "K9_CED0"), ("cedilla-3", "K9_CED3")):
            v[key] = pct(k9[k9.cond == cond]["pass"].mean())
        v["K9_CLEAN_MIN"] = min(v["K9_CLEAN0"], v["K9_CLEAN1"], v["K9_CLEAN3"])
        assert v["K9_CLEAN_MIN"] >= 90, "the post says the neighbours hardly mattered around a clean document"
    tu = every[every.task == "turns"]
    if len(tu):
        v["N_T12"] = tu.model.nunique()
        v["T12_CED_CLEAN"] = pct(tu[tu.cond == "cedilla>clean"]["pass"].mean())
        assert v["T12_CED_CLEAN"] >= 90, "the post says a cedilla first message rarely changed the next answer"

    # counts used in the text
    e4 = every[every.task == "echo4"]
    v["N_FLASH"] = int(sum(1 for m in set(e4.model) if M.line(m) == "Gemini Flash"))
    w = every[every.task == "wrong"]
    v["N_T13"] = w.model.nunique()
    if len(w) and w.model.nunique() >= 10:
        import task13 as T13  # noqa: E402
        wd = T13.prepare(w)
        p1, p2 = T13.paired(wd, "dot", "cedilla"), T13.paired(wd, "legacy", "cedilla")
        v["T13_CED_KEPT"], v["T13_DOT_KEPT"], v["T13_LEG_KEPT"] = f"{p1['b']:.0f}", f"{p1['a']:.1f}", f"{p2['a']:.1f}"
        v["T13_DOT_DIFF_LO"], v["T13_DOT_DIFF_HI"] = f"{-p1['hi']:.0f}", f"{-p1['lo']:.0f}"  # as a drop in points
        v["T13_MODELS_LOWER"], v["T13_MODELS"] = p1["models_lower"], p1["models"]
        v["T13_MODELS_HIGHER"] = p1["models_higher"]
        rep = wd[wd.variant.isin(["dot", "legacy"]) & (wd.sl_st > 0)]
        fixed = rep[[f"sl_st_{f}" for f in ("comma", "cedilla", "bare", "other")]].sum()
        v["T13_REPAIR_COMMA"] = f"{100 * fixed['sl_st_comma'] / fixed.sum():.0f}"
        for var, key in (("cedilla", "T13_CED_CLEAN"), ("dot", "T13_DOT_CLEAN"), ("legacy", "T13_LEG_CLEAN"),
                         ("cedilla+scoped", "T13_SCOPED"), ("cedilla+rule", "T13_FULL")):
            v[key] = pct(wd[wd.variant == var]["pass"].mean())
        assert p1["models_higher"] == 0, "the post says no model kept the dot below more often than the cedilla"
        others = []
        for m, g in wd.groupby("model"):
            sh = {var: g[(g.variant == var) & (g.sl_st > 0)] for var in ("dot", "legacy")}
            sh = {var: 100 * d.kept.sum() / d.sl_st.sum() if d.sl_st.sum() else 0.0 for var, d in sh.items()}
            if max(sh.values()) >= 10:
                others.append((max(sh.values()), f"{M.name(m)} ({sh['dot']:.0f} % of dotted letters, "
                                                 f"{sh['legacy']:.0f} % of mojibake letters)"))
        others = [t for _, t in sorted(others, reverse=True)]
        v["T13_OTHERS"] = " and ".join(others) if len(others) <= 2 else ", ".join(others[:-1]) + " and " + others[-1]
        v["T13_OTHERS_N"] = len(others)
        sonnet = wd[wd.model == "claude-sonnet-5-default"]
        if len(sonnet):
            for var, key in (("dot", "T13_SONNET5_DOT"), ("legacy", "T13_SONNET5_LEG")):
                d = sonnet[(sonnet.variant == var) & (sonnet.sl_st > 0)]
                v[key] = f"{100 * d.kept.sum() / d.sl_st.sum():.0f}"


def deepseek_reasoning():
    """DeepSeek-R1 returns its reasoning inline (<think>), and the raw run files keep it. For every answer to
    cedilla input: did the reasoning talk about the letters, and did the answer copy them?"""
    import glob
    from scoring import census as _census, visible as _visible

    def walk(o):
        if isinstance(o, dict):
            for c in o.get("conversations", []) or []:
                yield from c.get("requests", []) or []
            for sub in o.get("subruns", []) or []:
                yield from walk(sub)

    talk = re.compile(r"cedill|comma[- ]below|virgul|diacritic|encoding|unicode|orthograph", re.I)
    rows, thinks = [], []
    for task in ("romanian-comma-below-2-echo", "romanian-comma-below-7-echo-with-a-rule",
                 "romanian-comma-below-8-echo-four-inputs"):
        for f in glob.glob(str(ROOT / "results" / "raw" / task / "*" / "deepseek-r1-0528" / "*" / "*.run.json")):
            for r in walk(json.loads(pathlib.Path(f).read_text(encoding="utf-8"))):
                parts = r["contents"]
                system = " ".join(p.get("text", "") for m in parts if m["role"] == "CONTENT_ROLE_SYSTEM" for p in m["parts"])
                user = " ".join(p.get("text", "") for m in parts if m["role"] == "CONTENT_ROLE_USER" for p in m["parts"])
                out = " ".join(p.get("text", "") for m in parts if m["role"] not in ("CONTENT_ROLE_USER", "CONTENT_ROLE_SYSTEM")
                               for p in m["parts"])
                if not set(user) & set("şţŞŢ"):
                    continue
                m = re.search(r"<think>(.*?)(</think>|$)", out, re.S)
                think = m.group(1) if m else ""
                thinks.append(think)
                rows.append({"rule": "comma below" in system, "talks": bool(talk.search(think)),
                             "copied": _census(_visible(out))["cedilla"] > 0})
    return pd.DataFrame(rows), thinks


def verdict_vs(value: float, threshold: float, higher_is_held: bool, margin: float = 5.0) -> str:
    """held / failed against a threshold set when scoring; inconclusive within `margin` of it."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "too early"
    if abs(value - threshold) < margin:
        return "inconclusive"
    return "held" if (value >= threshold) == higher_is_held else "failed"


def predictions(every: pd.DataFrame) -> tuple[str, dict, str]:
    """The Round 2 predictions as written in the task descriptions, each scored against the data.

    The predictions were written as directions before the runs; the thresholds that turn a result into
    "held" or "failed" were set when scoring, and a result within 5 points of its threshold (or a rank
    correlation over fewer than 10 models) counts as inconclusive. Each prediction is scored on the data it
    names (task 9's and task 12's second predictions on task 2). Version steps count when they survive the
    Holm correction the post uses. Returns the table, the counts, and a sentence naming the verdicts that
    rest on little data (rank correlations get a permutation p-value for it).
    """
    from round2 import perm_spearman, perm_trend, purity, turkish_outcomes  # noqa: E402

    rows, verdicts = [], []
    thin = {}  # what the note under the table needs

    def names(models) -> str:
        n = sorted({M.name(m) for m in models})
        return " and ".join(n) if len(n) <= 2 else ", ".join(n[:-1]) + " and " + n[-1]

    def add(task, text, result, verdict):
        verdicts.append(verdict)
        shown = "**failed**" if verdict == "failed" else verdict
        rows.append(f"| {task} | {text} | {result} | {shown} |")

    e4 = every[every.task == "echo4"]
    if len(e4):
        per = e4.groupby(["model", "variant"])["pass"].mean().unstack() * 100
        low = per["clean"].min()
        lows = " and ".join(M.name(m) for m in per.index[per["clean"].round(6) == round(low, 6)])
        add(8, "Correct input stays near 100 % for every model.", f"lowest: {lows}, {low:.0f} %",
            verdict_vs(low, 95, True))
        a, c = 100 * e4[e4.variant == "ascii"]["pass"].mean(), 100 * e4[e4.variant == "cedilla"]["pass"].mean()
        add(8, "Cedilla input fails far more often than input without diacritics.",
            f"{a:.0f} % vs {c:.0f} % clean answers", verdict_vs(a - c, 15, True))
        pts = [(M.line(m), M.version(m), 100 * g[g.variant == "cedilla"]["pass"].mean()) for m, g in e4.groupby("model")]
        rho, p = perm_trend(pts)
        steps_f = ROOT / "results" / "round2_version_steps.csv"
        dn = up = dn0 = up0 = n_steps = 0
        if steps_f.exists():
            st = pd.read_csv(steps_f)
            st = st[st.kind == "version"]
            n_steps = len(st)
            dn0, up0 = int(((st.p < 0.05) & (st.change < 0)).sum()), int(((st.p < 0.05) & (st.change > 0)).sum())
            hs = holm(st)  # the correction the post's text uses for the same steps
            dn, up = int((hs.change < 0).sum()), int((hs.change > 0).sum())
        v = "inconclusive" if dn == up == 0 else "held" if up == 0 else "failed" if dn == 0 else "mixed"
        add(8, "Newer versions in a family copy the cedilla at least as often as older ones.",
            f"of {n_steps} upgrades, {dn} copied more and {up or 'none'} copied less after a correction for multiple tests "
            f"({dn0} and {up0} at p < 0.05 before it); no overall trend (rank correlation {rho:+.2f})", v)
        n90 = int((per["cedilla+rule"] >= 90).sum())
        add(8, "The one-sentence rule lifts cedilla input to at least 90 % for most models.",
            f"{n90} of {len(per)} models at 90 % or more", verdict_vs(100 * n90 / len(per), 50, True))

    k9 = every[every.task == "contagion"]
    if len(k9) and k9.model.nunique() >= 5:
        per = k9.groupby(["model", "cond"])["pass"].mean().unstack() * 100
        n90 = int((per["clean-3"] >= 90).sum())
        add(9, "With a clean target, answers stay clean for most models even when the other three documents are cedilla.",
            f"{n90} of {len(per)} models at 90 % or more", verdict_vs(100 * n90 / len(per), 50, True))
        e2 = every[(every.task == "echo") & (every.variant == "cedilla")]  # task 2, as registered
        if len(e2):
            whole = {}
            for m, g in e2[~e2["pass"].astype(bool)].groupby("model"):
                pur = [x for x in (purity(r) for r in g.response) if not np.isnan(x)]
                whole[m] = np.mean([x == 1.0 for x in pur]) if pur else np.nan
            j = pd.concat([pd.Series(whole, name="whole"), (100 - per["clean-3"]).rename("infected")], axis=1).dropna()
            r, p = perm_spearman(j.whole, j.infected) if len(j) >= 5 else (np.nan, np.nan)
            v = "too early" if np.isnan(r) else "inconclusive" if len(j) < 10 else ("held" if r >= 0.3 else "failed")
            hit = j.index[j.infected > 0]
            add(9, "The models that rewrote whole answers in cedilla in task 2 are the ones whose clean-target answers "
                   "get infected.",
                f"rank correlation {r:+.2f} over {len(j)} models; only {names(hit)} had infected answers", v)
            thin["k9"] = (v, p)
        a, b = 100 * k9[k9.cond == "cedilla-0"]["pass"].mean(), 100 * k9[k9.cond == "cedilla-3"]["pass"].mean()
        add(9, "A cedilla target is copied less when the other documents are clean.",
            f"{a:.0f} % vs {b:.0f} % clean answers", verdict_vs(a - b, 0, True))

    tr = every[every.task == "turkish"]
    if len(tr) and tr.model.nunique() >= 5:
        tt, _ = turkish_outcomes(tr)
        ok = {r: 100 * (tt[tt.rule == r].outcome == "correct").mean() for r in ("none", "rule", "scoped")}
        add(10, "Without a rule, Turkish replies keep ş.", f"{ok['none']:.0f} % correct", verdict_vs(ok["none"], 95, True))
        bad = tt[(tt.rule == "rule") & (tt.outcome == "turkish_with_comma")]
        add(10, "Task 7's rule makes some models write Turkish with the Romanian comma letter.",
            f"{bad.model.nunique()} of {tt.model.nunique()} models, {len(bad)} replies", "held" if len(bad) else "failed")
        ro = 100 * tr[(tr.lang == "ro") & (tr.rule == "scoped")]["pass"].mean()
        both = (verdict_vs(ok["scoped"], 95, True), verdict_vs(ro, 90, True))
        v = "failed" if "failed" in both else "inconclusive" if "inconclusive" in both else "held"
        add(10, "The scoped rule keeps Turkish intact and still fixes Romanian.",
            # one decimal: the threshold is 95 %, and a rounded "95 %" would hide how close it came
            f"Turkish {ok['scoped']:.1f} % correct (no rule: {ok['none']:.0f} %, full rule: {ok['rule']:.0f} %), "
            f"Romanian {ro:.0f} %", v)

    lk = every[every.task == "lookalike"]
    if len(lk) and lk.model.nunique() >= 5 and "cyrillic-names" in set(lk.variant):
        cl = 100 * lk[lk.variant == "clean"]["pass"].mean()
        add(11, "Correct English input stays near 100 %.", f"{cl:.0f} %", verdict_vs(cl, 95, True))
        cy, mo = 100 * lk[lk.variant == "cyrillic-names"]["pass"].mean(), 100 * lk[lk.variant == "mojibake"]["pass"].mean()
        add(11, "Cyrillic look-alikes are copied far more often than mojibake.",
            f"clean answers: {cy:.0f} % with look-alikes in the names, {mo:.0f} % with mojibake",
            verdict_vs(mo - cy, 15, True))
        if len(e4):
            per = lk.groupby(["model", "variant"])["pass"].mean().unstack()
            ced = e4[e4.variant == "cedilla"].groupby("model")["pass"].mean()
            j = pd.concat([per["cyrillic-names"].rename("cy"), ced.rename("ced")], axis=1).dropna()
            r, p = perm_spearman(j.cy, j.ced) if len(j) >= 5 else (np.nan, np.nan)
            v = "too early" if np.isnan(r) else "inconclusive" if len(j) < 10 else ("held" if r >= 0.3 else "failed")
            cn = lk[(lk.variant == "cyrillic-names") & lk.model.isin(j.index)]
            kept = cn[~cn["pass"].astype(bool)]
            add(11, "The models that copy the Romanian cedilla most also copy the look-alikes most.",
                f"rank correlation {r:+.2f} over {len(j)} models, resting on the {len(kept)} of {len(cn)} answers "
                f"that kept a look-alike ({kept.model.nunique()} models)", v)
            thin["lk"] = (v, p)

    tu = every[every.task == "turns"]
    if len(tu) and tu.model.nunique() >= 5:
        cc = tu[tu.cond == "cedilla>clean"]
        n_inf = int((cc.second_cedilla > 0).sum())
        inf = 100 * n_inf / len(cc)
        inf_first = 100 * (cc[cc.first_cedilla > 0].second_cedilla > 0).mean()
        who = cc[cc.second_cedilla > 0].model
        by = ("" if not len(who) else f", both {names(who)}" if n_inf == 2 and who.nunique() == 1
              else f", all {names(who)}" if who.nunique() == 1 else f", from {names(who)}")
        v = "held" if inf > 0 and inf_first > inf else "failed"
        add(12, "A cedilla first text infects some clean second summaries, mostly after a cedilla first summary.",
            f"{inf:.0f} % infected ({n_inf} of {len(cc)} conversations{by}); "
            f"{inf_first:.0f} % when the first summary was itself in cedilla", v)
        thin["turns"] = (v, n_inf, len(cc), by.replace(", both ", ", both from ").replace(", all ", ", all from "))
        e2 = every[(every.task == "echo") & (every.variant == "cedilla")]
        if len(e2):  # "copied less than in task 2", as registered
            ms = set(tu.model)
            base = 100 * e2[(e2.kind == "summary") & (e2.model.isin(ms))]["pass"].mean()
            prot = 100 * tu[tu.cond == "clean>cedilla"]["pass"].mean()
            add(12, "A clean first text does not protect a cedilla second text much.",
                f"{prot:.0f} % clean after a clean first text, {base:.0f} % on its own (the same models' task 2 summaries)",
                verdict_vs(prot - base, 15, False))

    w = every[every.task == "wrong"]
    if len(w) and w.model.nunique() >= 10:
        import task13 as T13  # noqa: E402
        wd = T13.prepare(w)
        p1, p2 = T13.paired(wd, "dot", "cedilla"), T13.paired(wd, "legacy", "cedilla")
        add(13, "The dot below is kept in a smaller share of s/t letters than the cedilla (paired, 95 % interval below zero).",
            f"{p1['a']:.1f} % vs {p1['b']:.1f} % of letters kept ({p1['diff']:+.0f} points, {p1['lo']:+.0f} to {p1['hi']:+.0f})",
            "held" if p1["hi"] < 0 else "failed")
        add(13, "The old mojibake is also kept less often than the cedilla.",
            f"{p2['a']:.1f} % vs {p2['b']:.1f} % ({p2['diff']:+.0f} points, {p2['lo']:+.0f} to {p2['hi']:+.0f})",
            "held" if p2["hi"] < 0 else "failed")
        rep = wd[wd.variant.isin(["dot", "legacy"]) & (wd.sl_st > 0)]
        fixed = rep[[f"sl_st_{f}" for f in ("comma", "cedilla", "bare", "other")]].sum()
        share = 100 * fixed["sl_st_comma"] / fixed.sum()
        add(13, "Repaired dot-below and mojibake letters become comma-below letters in at least 90 % of cases.",
            f"{share:.0f} % comma, {100 * fixed['sl_st_cedilla'] / fixed.sum():.1f} % cedilla", "held" if share >= 90 else "failed")
        sc = 100 * wd[wd.variant == "cedilla+scoped"]["pass"].mean()
        fu = 100 * wd[wd.variant == "cedilla+rule"]["pass"].mean()
        add(13, "Both rules give at least 90 % clean answers, and the scoped rule is within 5 points of the full rule.",
            f"scoped {sc:.0f} %, full {fu:.0f} %", "held" if sc >= 90 and fu >= 90 and abs(sc - fu) <= 5 else "failed")
        g = T13.own_words(wd, "cedilla")
        (na, wa), (ns, ws) = g["all"][1:], g["some"][1:]
        v5 = ("too early" if not na or not ns else
              "held" if 100 * wa / na >= 80 and 100 * ws / ns <= 30 else "failed")
        add(13, "In cedilla answers that keep every cedilla, at least 80 % of the model's own new s/t words have the cedilla; "
                "when they keep only some, at most 30 %.",
            f"{wa} of {na} vs {ws} of {ns} new words", v5)

    head = "| Task | Prediction | Result | |\n| --- | --- | --- | --- |"
    counts = {k: verdicts.count(k) for k in ("held", "failed", "mixed", "inconclusive", "too early")}
    counts["total"] = len(verdicts)

    # one sentence for under the table: the verdicts that rest on little data
    note = ""
    if {"k9", "lk", "turns"} <= set(thin):
        (v9, p9), (v11, p11), (v12, n_inf, n_cc, by) = thin["k9"], thin["lk"], thin["turns"]
        which = "of the predictions that held" if v9 == v11 == v12 == "held" else "of these verdicts"
        note = (f"Three {which} rest on very little: the rank correlations in tasks 9 and 11 could be chance "
                f"(permutation p = {p9:.2f} and {p11:.2f}), and the infection in task 12 is {n_inf} of {n_cc} "
                f"conversations{by}.")
    return head + "\n" + "\n".join(rows), counts, note


# (claim name, text that must appear in the post, with {} for the recomputed value key). The third
# version fills every number from post_values.json, so this list is short; sentences whose truth
# depends on the data are guarded by asserts in third_version_values() instead.
CLAIMS: list[tuple[str, str]] = [
    ("dose-response", "{K9_LOWER} of the {N_K9} models moved that way, none the other"),
]

# Every model output quoted in the post: (model slug, verbatim fragment). The fragment must occur in one of
# that model's answers in results/raw, and in the post.
# Fragments of DeepSeek-R1's reasoning quoted in the post (checked against the raw run files).
THINK_QUOTES = [
    "proper Romanian orthography with ș/ț commas below, not cedillas",
]

QUOTES = [
    ("claude-opus-5-default", "îndrumaţi"),
    ("claude-opus-5-default", "Şoferii sunt îndrumaţi să parcheze pe strada Mureşenilor sau lângă Gara Braşov."),
    ("gpt-oss-120b", "Șoferii sunt rugaţi să parcheze pe strada Mureșenilor și lângă Gara Brașov."),
    ("claude-opus-4-6-default", "îndrumaţi"),
    ("gpt-5.6-luna", "îndrumaţi"),
    ("gemini-3.7-flash", "muhteșem dağ manzaralı"),
    ("gemini-3.7-flash", "Șarap tadımı"),
    ("deepseek-r1-0528", "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare."),
    ("claude-opus-5-5-default", "Festivalul a avut loc la Sighişoara, iar biletele pentru ediţia de anul viitor se vor pune în vânzare în decembrie."),
    ("claude-opus-5-5-default", "Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie."),
]

# Numbers a reader sees that are not data: chance level, the size of the human test, round labels.
NUMBER_WHITELIST = {"50", "12"}


def number_scan(post: str, v: dict) -> list[str]:
    """Every percentage and every "k of n" in the visible text must be one of the computed values."""
    sys.path.insert(0, str(ROOT / "post"))
    from wordcount import visible_text  # noqa: E402
    vis, _ = visible_text(post)
    vis = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", vis)
    known = set(NUMBER_WHITELIST)
    for val in v.values():
        known |= set(re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", str(val)))
    bad = []
    for m in re.finditer(r"(\d+(?:,\d{3})*(?:\.\d+)?) ?%", vis):
        if m.group(1) not in known:
            bad.append(f"{m.group(0)!r} in ...{vis[max(0, m.start() - 50):m.end() + 10]!r}")
    for m in re.finditer(r"(\d+(?:,\d{3})*) of (?:the |its |their |my )?(\d+(?:,\d{3})*)", vis):
        for g in m.groups():
            if g not in known:
                bad.append(f"{m.group(0)!r} in ...{vis[max(0, m.start() - 50):m.end() + 10]!r}")
    return bad


def r1_values(r1l, v):
    """Round 1 numbers typed into the post as text."""
    import csv
    rows = [r for r in csv.DictReader(open(ROOT / "analysis" / "web_census.csv", encoding="utf-8")) if not r["error"]]
    shares = []
    for r in rows:
        ced = 0 if "wikipedia" in r["url"] else int(float(r["cedilla"]))  # Tolisi: s-cedilla is right in Talysh
        com = int(float(r["comma"]))
        shares.append(ced / (ced + com) if ced + com else 0.0)
    v["CENSUS_WITH"] = sum(1 for x in shares if x > 0)
    v["CENSUS_10"] = sum(1 for x in shares if x > 0.10)
    v["CENSUS_MAX"] = pct(max(shares))
    # which of those sites mark their pages as Romanian (analysis/web_lang.py, fetched 10 Oct)
    wl = ROOT / "analysis" / "web_lang.csv"
    if wl.exists():
        lang_rows = list(csv.DictReader(line for line in open(wl, encoding="utf-8") if not line.startswith("#")))
        assert len(lang_rows) == v["CENSUS_WITH"] and not any(r["error"] for r in lang_rows), \
            "the post counts the language of the same sites as the census"
        v["LANG_RO"] = sum(r["html_lang"].lower().startswith("ro") for r in lang_rows)
    g = r1l[r1l.model == "grok-4.20-0309-reasoning"]
    v["GROK_W"] = pct(g[g.task == "write"]["pass"].mean())
    v["GROK_SEE"] = pct(g[(g.task == "see") & (g.note == "all cedilla")]["pass"].mean())
    v["GROK_FIX"] = pct(g[(g.task == "fix") & (g.level == "L2_diacritics")]["pass"].mean())
    see = r1l[(r1l.task == "see") & r1l.note.isin(["both comma", "both cedilla"])]
    always = sorted(m for m, d in see.groupby("model") if d["pass"].astype(float).sum() == 0)
    v["SEE_ALWAYS_DIFF"] = ", ".join(M.name(m) for m in always)
    code = r1l[r1l.task == "code"]
    see = r1l[r1l.task == "see"]
    v["R1_SEE_CLEAN"] = pct(see[see.note == "clean"]["pass"].mean())
    v["R1_SEE_ONE"] = pct(see[see.note == "one cedilla word"]["pass"].mean())
    ident = see[see.note.isin(["both comma", "both cedilla"])]
    v["R1_IDENT_SAME"], v["R1_IDENT_N"] = int(ident["pass"].sum()), len(ident)
    v["R1_IDENT_PCT"] = pct(ident["pass"].mean())
    asc = see[see.note == "control: ascii identical"]
    v["R1_ASCII_SAME"], v["R1_ASCII_N"], v["R1_ASCII_PCT"] = int(asc["pass"].sum()), len(asc), pct(asc["pass"].mean())
    l1 = r1l[(r1l.task == "fix") & (r1l.level == "L1_proofread")]
    v["R1_PROOF"], v["R1_PROOF_K"], v["R1_PROOF_N"] = pct(l1["pass"].mean()), int(l1["pass"].sum()), len(l1)
    v["CODE_DECOMP_FAIL"] = int(sum(("decomposed_s" in (f or [])) for f in code.failed))
    full = code[code.score.astype(float) >= 0.999]
    v["CODE_C1_FULL"] = int((full.item_id == "C1_explicit").sum())
    v["CODE_C2_FULL"] = int((full.item_id == "C2_goal").sum())
    from round2 import mcnemar as _mcn
    piv = code.pivot_table(index="model", columns="item_id", values="score", aggfunc="first").astype(float)
    _, _, p = _mcn((piv["C1_explicit"] >= 0.999).astype(float), (piv["C2_goal"] >= 0.999).astype(float))
    v["CODE_P"] = f"{p:.2f}"


_SEE_PATTERN = {"codepoint": (re.compile(r"U\+([0-9A-Fa-f]{4,6})"), lambda x: "U+" + x.upper().rjust(4, "0")),
                "bool": (re.compile(r"\b(true|false|yes|no)\b", re.I), lambda x: "true" if x.lower() in ("true", "yes") else "false")}


def see_final(response: str, kind: str) -> str | None:
    """A See reply's final answer: the last "Answer: ...", else the first line if it holds one (replies that
    answer first and explain after), else the last U+XXXX or true/false. The task on Kaggle takes the first
    one anywhere in the reply, so a reply that lists every letter's code point before giving the right one
    counts as wrong there. (Taking the last one alone misreads the answer-first replies: "no visible
    differences" would turn a "true" into "false".)"""
    pat, norm = _SEE_PATTERN["codepoint" if kind == "codepoint" else "bool"]
    t = response or ""
    for line in reversed(re.findall(r"answer\s*[:*]*\s*\**\s*(.*)", t, re.I)):
        m = pat.search(line)
        if m:
            return norm(m.group(1))
    m = pat.search(next((line for line in t.splitlines() if line.strip()), ""))
    if m:
        return norm(m.group(1))
    found = pat.findall(t)
    return norm(found[-1]) if found else None


def see_final_values(r1l: pd.DataFrame, v: dict):
    """Task 4 (See) for the two models whose replies give the answer last: the score in the post's table
    (first match, as on Kaggle) and the score on each reply's final answer."""
    see = r1l[r1l.task == "see"]
    for m, key in (("deepseek-r1-0528", "SEE_DS"), ("gemini-3.5-flash-lite", "SEE_FL")):
        d = see[see.model == m]
        if len(d):
            v[f"{key}_TABLE"] = pct(d["pass"].astype(float).mean())
            v[f"{key}_FINAL"] = pct(np.mean([see_final(r, k) == a for r, k, a in zip(d.response, d.kind, d.answer)]))


def check(v: dict) -> int:
    post = (ROOT / "post" / "post-v3-dev.md").read_text(encoding="utf-8")
    bad = 0
    for problem in number_scan(post, v):
        bad += 1
        print("FAIL  number not in post_values.json:", problem)
    every = load(all_runs=True)
    plain = post.replace("**", "")
    traces = have_traces()
    _, thinks = deepseek_reasoning() if traces else (None, [])
    for fragment in THINK_QUOTES:
        if not traces:  # the reasoning is only in the run traces; the post can still be checked
            bad += fragment not in plain
            print(f"{'SKIP' if fragment in plain else 'FAIL'}  reasoning quote: {fragment[:60]}  "
                  "(needs the run traces, not in the repo)" + ("" if fragment in plain else "  (not in the post)"))
            continue
        found = any(fragment in t for t in thinks)
        ok = found and fragment in plain
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  reasoning quote: {fragment[:60]}" + ("" if found else "  (not in the data)")
              + ("" if fragment in plain else "  (not in the post)"))
    for model, fragment in QUOTES:
        found = every[(every.model == model) & every.response.fillna("").str.contains(fragment, regex=False)]
        ok = len(found) > 0 and fragment in plain
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  quote {model}: {fragment[:60]}"
              + ("" if len(found) else "  (not in the data)") + ("" if fragment in plain else "  (not in the post)"))
    for name, template in CLAIMS:
        try:
            text = template.format(**v)
        except KeyError as e:
            print(f"SKIP  {name}: no value for {e}")
            continue
        ok = text in post
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {name}: {text}")
    return bad


if __name__ == "__main__":
    vals = values()
    if "--values" in sys.argv:
        out = ROOT / "results" / "post_values.json"
        out.write_text(json.dumps(vals, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", out.name, json.dumps(vals, ensure_ascii=False)[:600])
    else:
        sys.exit(1 if check(vals) else 0)
