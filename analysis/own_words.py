"""Do the words a model adds itself follow the cedilla it copied? (the "picks up my keyboard" finding)

For every answer to a cedilla input (task 2 and task 8, no rule): its s/t words that also occur in
the source text, after folding diacritics ("source words"), and the s/t words it adds ("new
words"). An answer kept all, some or none of my cedillas, judged on its source words; new words
can't be copied, so their spelling shows what the model does on its own. Intervals are 95 %
percentile bootstraps over models.

Usage:  uv run --no-project --with pandas --with numpy python analysis/own_words.py
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
import items as I  # noqa: E402
from analyze import load  # noqa: E402
from round2 import ok_rows  # noqa: E402

RNG = np.random.default_rng(20261009)
COMMA, CEDILLA = set("șȘțȚ"), set("şŞţŢ")
_FOLD = str.maketrans({"ă": "a", "Ă": "A", "â": "a", "Â": "A", "î": "i", "Î": "I", "ș": "s", "Ș": "S",
                       "ț": "t", "Ț": "T", "ş": "s", "Ş": "S", "ţ": "t", "Ţ": "T"})
_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
TEXTS = {i: t for i, _, t in I.ECHO}
RAG = {f"Q{n:02d}": i for n, (i, _) in enumerate(I.ECHO_RAG, 1)}


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def fold(w: str) -> str:
    return nfc(w).translate(_FOLD).casefold()


def source_text(base_id: str) -> str:
    return TEXTS[RAG[base_id]] if base_id.startswith("Q") else TEXTS[base_id]


def origin(word: str, src: set[str]) -> str:
    """'source' (in the source after folding), 'inflected' (shares a 5-letter start with a source word,
    or every part of a hyphenated word is a source word), else 'new'. Inflected words reuse a copied
    stem, so only 'new' words count as the model's own. One more case: a stem whose ia becomes ie
    (Piața, Pieței) is too short for the 5-letter rule. task13.py keeps the rule as pre-registered."""
    k = fold(word)
    if k in src:
        return "source"
    if all(p in src for p in k.split("-")) or any(len(os.path.commonprefix([k, x])) >= 5 for x in src):
        return "inflected"
    if any(len(x) >= 5 and "ia" in x and k.startswith(x.replace("ia", "ie")[:-1]) for x in src):
        return "inflected"
    return "new"


def tokens(answer: str, source: str) -> tuple[list[str], list[str]]:
    """Forms ('comma' or 'cedilla') of the answer's s/t words: (source words, new words)."""
    src = {fold(w) for w in _WORD.findall(nfc(source))}
    out_src, out_new = [], []
    for w in _WORD.findall(nfc(answer)):
        letters = set(w)
        form = "cedilla" if letters & CEDILLA else "comma" if letters & COMMA else None
        if not form:
            continue
        o = origin(w, src)
        if o == "source":
            out_src.append(form)
        elif o == "new":
            out_new.append(form)
    return out_src, out_new


def answers(df: pd.DataFrame) -> pd.DataFrame:
    e = df[((df.task == "echo") | (df.task == "echo4")) & (df.variant == "cedilla")]
    rows = []
    for r in e.to_dict("records"):
        s, n = tokens(r["response"], source_text(r["base_id"]))
        kept = s.count("cedilla")
        group = None if not s else "all" if kept == len(s) else "some" if kept else "none"
        rows.append({"model": r["model"], "task": r["task"], "base_id": r["base_id"], "group": group,
                     "n_source": len(s), "kept": kept, "n_new": len(n), "new_cedilla": n.count("cedilla")})
    return pd.DataFrame(rows)


def boot_share(d: pd.DataFrame, B: int = 4000) -> tuple[float, float]:
    g = d.groupby("model")[["new_cedilla", "n_new"]].sum()
    if len(g) < 2:
        return (float("nan"), float("nan"))
    idx = RNG.integers(0, len(g), size=(B, len(g)))
    v = g.values[idx].sum(axis=1)
    return tuple(100 * np.percentile(v[:, 0] / v[:, 1], [2.5, 97.5]))


def summary(a: pd.DataFrame) -> dict:
    out = {}
    copying = a[(a.kept > 0) & (a.n_source >= 2)]
    out["all_or_none"] = (int((copying.group == "all").sum()), len(copying))
    for g in ("all", "some", "none"):
        d = a[(a.group == g) & (a.n_new > 0)]
        out[g] = (int(d.new_cedilla.sum()), int(d.n_new.sum()), len(d), d.model.nunique(), boot_share(d))
    both = a[a.n_new > 0].groupby(["model", "group"])[["new_cedilla", "n_new"]].sum().unstack("group")
    if ("n_new", "all") in both and ("n_new", "some") in both:
        both = both[both[("n_new", "all")].fillna(0).gt(0) & both[("n_new", "some")].fillna(0).gt(0)]
        out["within"] = {m: (int(r[("new_cedilla", "all")]), int(r[("n_new", "all")]),
                             int(r[("new_cedilla", "some")]), int(r[("n_new", "some")])) for m, r in both.iterrows()}
    return out


def report(name: str, s: dict):
    k, n = s["all_or_none"]
    print(f"{name}: answers that kept at least one of my cedillas (and had 2+ source words) kept all of them: "
          f"{k}/{n} = {100 * k / n:.0f} %")
    for g, label in (("all", "kept all"), ("some", "kept some"), ("none", "kept none")):
        c, t, na, nm, ci = s[g]
        if t:
            print(f"  {label:9s}: new words with the cedilla {c}/{t} = {100 * c / t:.0f} % "
                  f"(95 % CI {ci[0]:.0f}-{ci[1]:.0f}), {na} answers, {nm} models")
    for m, (ca, ta, cs, ts) in sorted(s.get("within", {}).items(), key=lambda x: -x[1][1]):
        print(f"    same model, {m}: kept all {ca}/{ta}, kept some {cs}/{ts}")


def main():
    a = answers(ok_rows(load(all_runs=True)))
    report("Tasks 2 and 8", summary(a))
    report("Task 8 only", summary(a[a.task == "echo4"]))


if __name__ == "__main__":
    main()
