"""Does a Romanian-only fix leave Turkish alone? Measured on the models' real answers.

fix_naive     every ş ţ becomes ș ț (the usual one-line fix, and the post's first version).
fix_romanian  the same swap, sentence by sentence, skipping sentences that contain a letter
              Romanian never uses (ı ğ ç ö ü). This is the function the post shows.

Turkish answers: the bot's own correct Turkish replies without a rule (task 10, where ş is right), the
base the post's numbers use; every Turkish reply under all three rules is printed after them. Romanian
answers: task 8's answers to cedilla input that kept at least one cedilla (task 10's Romanian replies
are included but none has a cedilla). check_claims.py writes the same numbers to post_values.json (FIX_*).

Usage:  uv run --no-project --with pandas --with numpy python analysis/fix_check.py
"""

from __future__ import annotations

import re
import sys
import unicodedata

sys.path.insert(0, "analysis")
sys.path.insert(0, "src")
from analyze import load  # noqa: E402
from round2 import ok_rows, turkish_outcomes  # noqa: E402

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


def turkish_base(df):
    """The bot's own correct Turkish replies without a rule (task 10): the post's base, as in chart-fixes."""
    tt, _ = turkish_outcomes(df[df.task == "turkish"])
    return tt[(tt.rule == "none") & (tt.outcome == "correct")]


def romanian_base(df):
    """Romanian answers with at least one cedilla letter: task 8 on cedilla input, and task 10's Romanian replies."""
    ro = df[((df.task == "echo4") & (df.variant == "cedilla")) | ((df.task == "turkish") & (df.lang == "ro"))]
    return ro[ro.response.fillna("").map(lambda r: has_cedilla(unicodedata.normalize("NFC", r)))]


def altered_sentences(text: str, f) -> list[str]:
    text = unicodedata.normalize("NFC", text or "")
    return [s.strip() for s in SENTENCE.findall(text) if f(s) != s]


def is_hos(text: str, f=fix_romanian) -> bool:
    """A reply the fix changes in a sentence with "hoş" (Hoş geldiniz, welcome; hoş bulduk): short greetings
    with no ı ğ ç ö ü to mark them as Turkish."""
    return any("hoş" in s.casefold() for s in altered_sentences(text, f))


def self_test():
    mixed = "Vă aşteptăm la Braşov! Teşekkür ederiz, görüşürüz.\nŞtiţi unde e gara?"
    assert fix_romanian(mixed) == "Vă așteptăm la Brașov! Teşekkür ederiz, görüşürüz.\nȘtiți unde e gara?"
    assert fix_naive(mixed).count("ş") == 0 and "Teșekkür" in fix_naive(mixed)
    assert fix_romanian("s" + chr(0x327) + "i") == "și"  # a decomposed cedilla is fixed too (NFC first)
    # a Romanian sentence quoting Zürich keeps its ş (the known gap) but loses its ţ
    assert fix_romanian("La Zürich şi la Constanţa.") == "La Zürich şi la Constanța."
    # a Turkish greeting without ı ğ ç ö ü is changed (the known gap on the other side)
    assert fix_romanian("Hoş geldiniz!") == "Hoș geldiniz!" and is_hos("Hoş geldiniz!")


def main():
    self_test()
    df = ok_rows(load(all_runs=True))
    tr, ro = turkish_base(df), romanian_base(df)
    tr_text = [unicodedata.normalize("NFC", r) for r in tr.response.fillna("")]
    print(f"Turkish replies (the bot's own correct replies without a rule, the post's base): {len(tr)} "
          f"from {tr.model.nunique()} models")
    print(f"Romanian answers with a cedilla: {len(ro)} from {ro.model.nunique()} models\n")
    for name, f in {"fix_naive": fix_naive, "fix_romanian": fix_romanian}.items():
        altered = [(m, r) for m, r in zip(tr.model, tr_text) if f(r) != r]
        left = [r for r in ro.response.fillna("") if has_cedilla(f(r))]
        print(f"{name:13s} Turkish replies altered: {len(altered):3d}/{len(tr)}   "
              f"Romanian answers still with a cedilla: {len(left)}/{len(ro)}")
        if name == "fix_romanian":
            for m, r in altered:
                print(f"    altered ({m}): " + " | ".join(altered_sentences(r, f))[:160])
            hos = sum(is_hos(r, f) for _, r in altered)
            print(f"    {hos} of the {len(altered)} are greetings with \"hoş\" (no ı ğ ç ö ü in the sentence)")
        for r in left[:3]:
            print("    missed:", " | ".join(s.strip() for s in SENTENCE.findall(unicodedata.normalize("NFC", r))
                                           if has_cedilla(f(s)))[:160])
    # every Turkish reply, under all three rules (not the post's base: these include broken replies)
    every_tr = df[(df.task == "turkish") & (df.lang == "tr")]
    text = [unicodedata.normalize("NFC", r) for r in every_tr.response.fillna("")]
    print(f"\nEvery Turkish reply, all three rules ({len(every_tr)} from {every_tr.model.nunique()} models): "
          f"fix_naive altered {sum(fix_naive(r) != r for r in text)}, "
          f"fix_romanian altered {sum(fix_romanian(r) != r for r in text)}")


if __name__ == "__main__":
    main()
