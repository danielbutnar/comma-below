"""Does a Romanian-only fix leave Turkish alone? Measured on the models' real answers.

fix_naive     every ş ţ becomes ș ț (the usual one-line fix, and the post's first version).
fix_romanian  the same swap, sentence by sentence, skipping sentences that contain a letter
              Romanian never uses (ı ğ ç ö ü). This is the function the post shows.

Turkish answers come from task 10 (replies to Turkish guests, where ş is right); Romanian answers
are task 8's cedilla answers that kept at least one cedilla, plus task 10's Romanian replies.

Usage:  uv run --no-project --with pandas --with numpy python analysis/fix_check.py
"""

from __future__ import annotations

import re
import sys
import unicodedata

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
from round2 import ok_rows  # noqa: E402

CEDILLA_TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")
T_ONLY = str.maketrans("ţŢ", "țȚ")  # Turkish has no ţ, so it is wrong in any sentence (since 10 Oct)
NOT_ROMANIAN = set("ıİğĞçÇöÖüÜ")
SENTENCE = re.compile(r"[^.!?\n]+")


def fix_naive(text: str) -> str:
    return unicodedata.normalize("NFC", text).translate(CEDILLA_TO_COMMA)


def fix_romanian(text: str) -> str:
    """Swap the cedilla for the comma; in a sentence with a letter Romanian never uses, swap only ţ."""
    text = unicodedata.normalize("NFC", text)
    return SENTENCE.sub(lambda m: m.group(0).translate(T_ONLY if set(m.group(0)) & NOT_ROMANIAN
                                                       else CEDILLA_TO_COMMA), text)


def has_cedilla(text: str) -> bool:
    return any(c in text for c in "şŞţŢ")


def self_test():
    mixed = "Vă aşteptăm la Braşov! Teşekkür ederiz, görüşürüz.\nŞtiţi unde e gara?"
    assert fix_romanian(mixed) == "Vă așteptăm la Brașov! Teşekkür ederiz, görüşürüz.\nȘtiți unde e gara?"
    assert fix_naive(mixed).count("ş") == 0 and "Teșekkür" in fix_naive(mixed)
    assert fix_romanian("s" + chr(0x327) + "i") == "și"  # a decomposed cedilla is fixed too (NFC first)
    # a Romanian sentence quoting Zürich keeps its ş (the known gap) but loses its ţ
    assert fix_romanian("La Zürich şi la Constanţa.") == "La Zürich şi la Constanța."


def main():
    self_test()
    df = ok_rows(load(all_runs=True))
    tr = df[(df.task == "turkish") & (df.lang == "tr")]
    ro = df[((df.task == "echo4") & (df.variant == "cedilla")) | ((df.task == "turkish") & (df.lang == "ro"))]
    ro = ro[ro.response.fillna("").map(lambda r: has_cedilla(unicodedata.normalize("NFC", r)))]
    print(f"Turkish answers: {len(tr)} from {tr.model.nunique()} models; "
          f"Romanian answers with a cedilla: {len(ro)} from {ro.model.nunique()} models\n")
    fixes = {"fix_naive": fix_naive, "fix_romanian": fix_romanian}
    for name, f in fixes.items():
        tr_text = tr.response.fillna("").map(lambda r: unicodedata.normalize("NFC", r))
        altered = [r for r in tr_text if f(r) != r]
        left = [r for r in ro.response.fillna("") if has_cedilla(f(r))]
        print(f"{name:40s} Turkish answers altered: {len(altered):4d}/{len(tr)}   "
              f"Romanian answers still with a cedilla: {len(left):4d}/{len(ro)}")
        for r in altered[:3] if name != "fix_naive" else []:
            print("    altered:", " | ".join(s.strip() for s in SENTENCE.findall(r) if f(s) != s)[:160])
        for r in left[:3]:
            print("    missed:", " | ".join(s.strip() for s in SENTENCE.findall(unicodedata.normalize("NFC", r))
                                           if has_cedilla(f(s)))[:160])


if __name__ == "__main__":
    main()
