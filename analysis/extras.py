"""Numbers for the post's newer paragraphs, added to the ones check_claims.py computes.

check_claims.values() calls add(v, every, latest) with every = ok_rows(load(all_runs=True)) and
latest = ok_rows(load()). Every value is formatted as the post shows it: ints for percentages,
plain strings for names and lists.

Usage (prints these values only):  uv run --no-project --with pandas --with numpy python analysis/extras.py
"""

from __future__ import annotations

import math
import csv
import difflib
import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
import items as I  # noqa: E402
import models as M  # noqa: E402
import own_words as OW  # noqa: E402
import task13 as T13  # noqa: E402
from analyze import load  # noqa: E402
from round2 import mcnemar, ok_rows, spearman  # noqa: E402
from scoring import visible, words  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_R1 = {"grok-4.6", "grok-4.5-0708", "gpt-oss-120b"}  # as in check_claims.py
S_LETTERS, T_LETTERS = set("șȘşŞ"), set("țȚţŢ")
TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")
# the talk regex of check_claims.deepseek_reasoning()
TALK = re.compile(r"cedill|comma[- ]below|virgul|diacritic|encoding|unicode|orthograph", re.I)
# a gpt-oss-120b answer to my correctly typed text (task 8, Q01-E07), checked against the data below
OSS_EXAMPLE = "Șoferii sunt rugaţi să parcheze pe strada Mureșenilor și lângă Gara Brașov."



# town and street names in my texts (src/items.py), comma-below spelling, folded; a word starting with one is a name
PLACE_STEMS = ("brașov", "bucureșt", "iași", "mureș", "râșnov", "sighișoar", "timiș", "transfăgărășan")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 % Wilson interval for k of n, in %."""
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (100 * (c - h) / d, 100 * (c + h) / d)

def pct(x) -> int:
    return int(round(100 * float(x)))


def _and(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def st_source_words(df: pd.DataFrame) -> pd.DataFrame:
    """Per answer: its source words (own_words.origin) with an s or a t diacritic, and how many of each kept the
    cedilla. A word with both letters counts once on each side. și is left out: it is the commonest word, and a
    model writes it whether or not my text had it."""
    rows = []
    for r in df.to_dict("records"):
        src = {OW.fold(w) for w in words(OW.source_text(r["base_id"]))}
        n = {"s_n": 0, "s_c": 0, "t_n": 0, "t_c": 0}
        for w in words(r["response"]):
            letters = set(w)
            if not letters & (S_LETTERS | T_LETTERS) or OW.fold(w) == "si" or OW.origin(w, src) != "source":
                continue
            for x, group in (("s", S_LETTERS), ("t", T_LETTERS)):
                if letters & group:
                    n[f"{x}_n"] += 1
                    n[f"{x}_c"] += bool(letters & group & OW.CEDILLA)
        rows.append({"model": r["model"], "base_id": r["base_id"], **n})
    return pd.DataFrame(rows)


def boot_s_minus_t(d: pd.DataFrame) -> tuple[float, float]:
    """task13's cluster bootstrap of a difference of two shares, over prompts, with its own seed so the
    interval doesn't depend on what ran before."""
    saved, T13.RNG = T13.RNG, np.random.default_rng(20261010)
    try:
        return T13.boot_ratio_diff(d, "base_id", "s_c", "s_n", "t_c", "t_n")
    finally:
        T13.RNG = saved


def stands_for(answer: str, source: str, word: str) -> str:
    """The source word an answer's word replaces, from difflib's alignment of the two word lists (folded)."""
    a, s = words(answer), words(source)
    sm = difflib.SequenceMatcher(a=[OW.fold(w) for w in s], b=[OW.fold(w) for w in a], autojunk=False)
    i = a.index(word)
    for tag, s0, s1, a0, a1 in sm.get_opcodes():
        if tag == "replace" and a0 <= i < a1 and s1 - s0 == 1:
            return s[s0]
    raise AssertionError(f"no single source word lines up with {word}")


def add(v: dict, every: pd.DataFrame, latest: pd.DataFrame) -> None:
    e4 = every[every.task == "echo4"]
    c4 = e4[e4.variant == "cedilla"]
    r1e = every[~every.model.isin(EXCLUDE_R1)]
    r1l = latest[~latest.model.isin(EXCLUDE_R1)]

    # a. ş against ţ. Task 8 answers to cedilla input, every run, source words only (și left out).
    st = st_source_words(c4)
    # % of source words with an s letter that came back with the cedilla ş
    v["ST_S_KEPT"] = pct(st.s_c.sum() / st.s_n.sum())
    # % of source words with a t letter that came back with the cedilla ţ
    v["ST_T_KEPT"] = pct(st.t_c.sum() / st.t_n.sum())
    # 95 % interval of S minus T in points, bootstrapping the 22 prompts (S and T of a prompt move together)
    lo, hi = boot_s_minus_t(st)
    v["ST_DIFF_LO"], v["ST_DIFF_HI"] = int(round(lo)), int(round(hi))
    both = st[(st.s_n > 0) & (st.t_n > 0)]
    s_only = (both.s_c == both.s_n) & (both.t_c == 0)
    t_only = (both.t_c == both.t_n) & (both.s_c == 0)
    # answers that kept the cedilla on every s source word and fixed every t source word
    v["ST_S_ONLY"] = int(s_only.sum())
    # answers that kept the cedilla on every t source word and fixed every s source word
    v["ST_T_ONLY"] = int(t_only.sum())
    # exact two-sided sign test of ST_S_ONLY against ST_T_ONLY (round2.mcnemar on the two disjoint flags)
    p = mcnemar(s_only.astype(float), t_only.astype(float))[2]
    v["ST_SPLIT_P"] = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
    # task 13's cedilla control: a fresh run of task 8's summaries and document questions
    st13 = st_source_words(every[(every.task == "wrong") & (every.variant == "cedilla")])
    # % of source words with an s letter that came back with ş, task 13's cedilla control
    v["T13_S_KEPT"] = pct(st13.s_c.sum() / st13.s_n.sum())
    # % of source words with a t letter that came back with ţ, task 13's cedilla control
    v["T13_T_KEPT"] = pct(st13.t_c.sum() / st13.t_n.sum())

    # b. The three cleanest models on task 8 (TOP_NAMES, from the same table) and their next versions.
    t = pd.read_csv(ROOT / "results" / "round2_echo4_models.csv")
    t = t[t.model.isin(set(e4.model))]
    top = t[t.cedilla >= t.cedilla.max() - 0.01].sort_values("name")
    by = t.set_index("model")["cedilla"]  # the basis of the V_* keys: every run of the same 22 prompts
    nxt = []
    for m in top.model:
        newer = sorted((M.version(x), x) for x in by.index if M.line(x) == M.line(m) and M.version(x) > M.version(m))
        assert M.line(m) in M.VERSION_LINES and newer, f"the post says {M.name(m)} is the older half of a pair"
        nxt.append(newer[0][1])  # the next version up in the same line
    # clean % on cedilla input of the next version of each TOP_NAMES model, in TOP_NAMES order ("55, 59 and 64 %")
    v["OLDER3_NEXT"] = _and([f"{by[m]:.0f}" for m in nxt]) + " %"
    # the names of those next versions, in the same order
    v["OLDER3_NEXT_NAMES"] = _and([M.name(m) for m in nxt])

    # c. gpt-oss brings its own cedilla; Claude Haiku 4.5 too.
    oss = e4[e4.model.isin(["gpt-oss-120b", "gpt-oss-20b"]) & (e4.variant == "clean")]
    # % of the two gpt-oss models' answers (pooled) to correctly typed task 8 input that contain a cedilla letter
    v["OSS_CLEAN_IN"] = pct((oss.cedilla > 0).mean())
    # the same as a count: answers with a cedilla, answers
    v["OSS_CLEAN_IN_K"], v["OSS_CLEAN_IN_N"] = int((oss.cedilla > 0).sum()), len(oss)
    hit = oss[oss.response.fillna("").str.contains(OSS_EXAMPLE, regex=False)]
    ced = [w for w in words(OSS_EXAMPLE) if set(w) & OW.CEDILLA]
    assert len(hit) and ced, "the quoted sentence is a gpt-oss answer to correct input, with a cedilla"
    assert all(w.translate(TO_COMMA) in words(OW.source_text(hit.iloc[0].base_id)) for w in ced), \
        "my text spelled the quoted cedilla word with the comma"
    # a verbatim gpt-oss answer to correct input, with a cedilla on a word my text spelled with the comma
    v["OSS_EXAMPLE"] = OSS_EXAMPLE
    # that word, as the model wrote it
    v["OSS_EXAMPLE_WORD"] = ced[0]
    h = e4[(e4.model == "claude-haiku-4-5-20251001") & (e4.variant == "ascii")]
    # Claude Haiku 4.5's answers to task 8 input with no diacritics that contain a cedilla letter, and all of them
    v["HAIKU_ASCII_CED"], v["HAIKU_ASCII_N"] = int((h.cedilla > 0).sum()), len(h)

    # d. Task 12: the clean second summaries that picked up a cedilla after a cedilla first text.
    texts = {i: x for i, _, x in I.ECHO}
    cc = every[(every.task == "turns") & (every.cond == "cedilla>clean")]
    inf = cc[cc.second_cedilla > 0]
    # infected conversations, and all cedilla>clean conversations
    v["T12_INF_N"], v["T12_INF_TOTAL"] = len(inf), len(cc)
    assert inf.model.nunique() == 1, "the post names one model for the infected conversations"
    # the model that wrote them
    v["T12_MODEL"] = M.name(inf.model.iloc[0])
    found = []  # (already in the model's own first summary, cedilla word, the clean text's word in its place)
    for r in inf.sort_values("pair_id").to_dict("records"):
        first, second = r["pair_id"][:3], r["pair_id"][3:]
        for w in (w for w in words(r["response"]) if set(w) & OW.CEDILLA):
            assert all(OW.fold(w) not in {OW.fold(x) for x in words(texts[i])} for i in (first, second)), \
                f"{w} is a word of the model's own, in neither text"
            own_first = OW.fold(w) in {OW.fold(x) for x in words(r["first"])}
            found.append((own_first, w, stands_for(r["response"], texts[second], w)))
    assert len({w for _, w, _ in found}) == 1, "the post quotes one word"
    pure = [f for f in found if not f[0]] or found
    # the cedilla word it wrote, which is in neither text of the conversation
    v["T12_WORD"] = pure[0][1]
    # the clean second text's word in its place, where the model's own first summary didn't have the word either
    v["T12_SRC_WORD"] = pure[0][2]
    # infections whose cedilla word was already in the model's own first summary
    v["T12_FROM_FIRST"] = sum(f[0] for f in found)

    # e. Qwen 3 Next with reasoning (Thinking) and without (Instruct), task 8 cedilla input, every run.
    raw = load(all_runs=True)
    q = raw[(raw.task == "echo4") & (raw.model == "qwen3-next-80b-a3b-thinking") & raw["error"].isna()]
    empty = q.response.fillna("").astype(str).str.strip() == ""
    done = c4[c4.model == "qwen3-next-80b-a3b-thinking"]
    # Thinking: clean answers, and answers with visible text
    v["QWEN_T_DONE_K"], v["QWEN_T_DONE_N"] = int(done["pass"].astype(bool).sum()), len(done)
    # Thinking: answers left empty (it thought past the 8,192-token cap)
    v["QWEN_T_EMPTY"] = int(empty[q.variant == "cedilla"].sum())
    # Thinking over all four inputs: prompts with a visible answer, prompts sent
    v["QWEN_T_ANSWERED"], v["QWEN_T_PROMPTS"] = int((~empty).sum()), len(q)
    # Instruct: % of answers clean
    v["QWEN_I_CLEAN"] = pct(c4[c4.model == "qwen3-next-80b-a3b-instruct"]["pass"].mean())

    # f. Spotting the cedilla against keeping it out, round one models (the basis of check_claims' SPOT_COPY_RHO).
    see_m = r1l[r1l.task == "see"].groupby("model")["pass"].mean()
    ech_m = r1e[(r1e.task == "echo") & (r1e.variant == "cedilla")].groupby("model")["pass"].mean()
    jj = pd.concat([see_m.rename("see"), ech_m.rename("echo")], axis=1).dropna()
    rho = spearman(jj.see, jj.echo)
    rx, ry = jj.see.rank().values, jj.echo.rank().values
    rng = np.random.default_rng(20261010)
    perm = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(20000)])
    # rank correlation between a model's task 4 (See) score and its clean share on cedilla input in task 2
    v.setdefault("SPOT_COPY_RHO", f"{rho:.2f}")
    assert v["SPOT_COPY_RHO"] == f"{rho:.2f}", "the same correlation as check_claims computes"
    # the number of models it is over
    v["SPOT_COPY_N"] = len(jj)
    # its two-sided permutation p-value
    v["SPOT_COPY_P"] = f"{(np.abs(perm) >= abs(rho) - 1e-12).mean():.2f}"

    # g. The within-model own-words check (WITHIN_N in check_claims): models with 10+ new words in both groups.
    within = OW.summary(OW.answers(every)).get("within", {})
    two = sorted(((m, x) for m, x in within.items() if x[1] >= 10 and x[3] >= 10), key=lambda t: -t[1][1])
    # their names
    v["OWN_WITHIN_NAMES"] = _and([M.name(m) for m, _ in two])
    # % of their new words with the cedilla when the answer kept all of mine, against when it kept some
    v["OWN_WITHIN_PCTS"] = "; ".join(f"{M.name(m)}: {pct(x[0] / x[1])} % against {pct(x[2] / x[3])} %"
                                     for m, x in two)

    # h. Task 8, cedilla input, every run (the basis of E4_REPLY / E4_SUMMARY / E4_RAG).
    for kind, key in (("reply", "KIND_REPLY"), ("summary", "KIND_SUM"), ("rag", "KIND_RAG")):
        d = c4[c4.kind == kind]
        # % of answers clean, for this kind of prompt
        v[key] = pct(d["pass"].mean())
        # the number of prompts of this kind
        v[key + "_PROMPTS"] = d.base_id.nunique()

    # i. How far one run's rate can be trusted. Task 8, cedilla input, each model's latest run.
    el = latest[(latest.task == "echo4") & (latest.variant == "cedilla")]
    g = el.assign(ok=el["pass"].astype(bool)).groupby("model")["ok"].agg(["sum", "count"])
    ci = np.array([wilson(int(k), int(n)) for k, n in zip(g["sum"], g["count"])])
    pooled = 100 * c4["pass"].mean()  # E4_CED, the rate the post quotes
    # models whose 95 % Wilson interval lies wholly above the pooled rate, and wholly below it
    v["N_CI_ABOVE"], v["N_CI_BELOW"] = int((ci[:, 0] > pooled).sum()), int((ci[:, 1] < pooled).sum())
    # models whose 95 % Wilson interval leaves out the pooled rate
    v["N_CI_EXCLUDE"] = v["N_CI_ABOVE"] + v["N_CI_BELOW"]
    # median width of those intervals, in points
    v["CI_WIDTH_MED"] = int(round(float(np.median(ci[:, 1] - ci[:, 0]))))
    runs = e4.groupby("model").run_id.nunique()
    assert runs.max() <= 2, "the post counts models with one and two runs"
    # models with one task 8 run, and with two
    v["N_SINGLE_RUN"], v["N_DOUBLE_RUN"] = int((runs == 1).sum()), int((runs == 2).sum())

    # j. The web census (analysis/web_census.csv): sites I tried to fetch, and sites that loaded.
    rows = list(csv.DictReader(open(ROOT / "analysis" / "web_census.csv", encoding="utf-8")))
    # front pages fetched, and front pages that loaded without an error (the 35 the census measures)
    v["CENSUS_FETCHED"], v["CENSUS_OK"] = len(rows), sum(1 for r in rows if not r["error"])

    # k. Task 3, "Proofread" (the answers behind R1_PROOF): answers that mention the letters or the encoding.
    l1 = r1l[(r1l.task == "fix") & (r1l.level == "L1_proofread")]
    says = l1.response.fillna("").map(lambda r: bool(TALK.search(visible(r))))
    # answers that mention them, and all answers
    v["PROOF_MENTION"], v["PROOF_MENTION_N"] = int(says.sum()), len(l1)
    # the models that wrote them
    v["PROOF_MENTION_MODELS"] = _and(sorted({M.name(m) for m in l1[says].model})) if says.any() else "no model"

    # l. Task 11, document answers, every run (the basis of LK_MOJI_COPIED_RAG).
    lk = every[(every.task == "lookalike") & (every.kind == "rag")]
    # % of answers to Cyrillic look-alike input (both variants) that kept a Cyrillic letter
    v["LK_CYR_COPIED_RAG"] = pct(1 - lk[lk.variant.isin(["cyrillic-all", "cyrillic-names"])]["pass"].mean())
    # % that kept a Cyrillic letter when only the names were Cyrillic: the same words the mojibake touches
    v["LK_CYR_NAMES_COPIED_RAG"] = pct(1 - lk[lk.variant == "cyrillic-names"]["pass"].mean())

    # m. "An answer from a document should quote it": task 8 cedilla input, every run. % of answers that are clean,
    # or whose every cedilla word is a place name from my texts (counting a kept name as a fair quote)
    def name_only(r) -> bool:
        ws = [w.translate(TO_COMMA).casefold() for w in (r.cedilla_words or [])]
        return bool(ws) and all(w.startswith(PLACE_STEMS) for w in ws) and not r.lookalike
    v["E4_CED_NAMES_OK"] = pct(np.mean([bool(r.pass_) or name_only(r) for r in c4.rename(columns={"pass": "pass_"}).itertuples()]))

    # n. The îndrumaţi move: models other than Claude Opus 5 that wrote the cedilla word for "directed" in a
    # summary of E07 typed with cedillas (tasks 2 and 8), where my text said "rugați"
    e07 = every[every.task.isin(["echo", "echo4"]) & (every.variant == "cedilla") & (every.base_id == "E07")]
    movers = sorted({m for m, r in zip(e07.model, e07.response.fillna("")) if "îndrumaţi" in r} - {"claude-opus-5-default"})
    v["N_INDRUMATI_OTHER"] = len(movers)
    # their names, for the record
    v["INDRUMATI_OTHER_NAMES"] = _and([M.name(m) for m in movers]) if movers else "none"
    # the same count as a word that can start a sentence ("Seven")
    v["N_INDRUMATI_WORD"] = (["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"][len(movers)]
                             if len(movers) <= 10 else str(len(movers)))

    # o. Task 12's control: chats with no cedilla anywhere (clean>clean) where an answer still had a cedilla
    tu = every[every.task == "turns"]
    ctrl = tu[tu.cond == "clean>clean"]
    hit = ctrl[(ctrl.first_cedilla > 0) | (ctrl.second_cedilla > 0)]
    v["T12_CTRL_N"], v["T12_CTRL_TOTAL"] = len(hit), len(ctrl)
    v["T12_CTRL_MODELS"] = _and(sorted({M.name(m) for m in hit.model})) if len(hit) else "none"

    # p. Grok 4.20 with reasoning on task 8 alone, the same run basis as V_GROK_NR (which only ran task 8)
    g = c4[c4.model == "grok-4.20-0309-reasoning"]
    if len(g):
        v["V8_GROK_R"] = pct(g["pass"].mean())


if __name__ == "__main__":
    vals: dict = {}
    add(vals, ok_rows(load(all_runs=True)), ok_rows(load()))
    print(json.dumps(vals, ensure_ascii=False, indent=1))
