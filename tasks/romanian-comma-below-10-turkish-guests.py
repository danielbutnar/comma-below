# %% [markdown]
# # Romanian Comma Below 10: Turkish Guests
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** the cedilla letter is wrong in Romanian and right in Turkish (*te&#x015F;ekk&#x00FC;r*, *&#x015F;ehir*). Eight Turkish guest messages are answered with no rule, with task 7's rule (*never &#x015F; or &#x0163;*), and with a rule scoped to Romanian; six Romanian messages typed with cedilla are answered under both rules. Does the fix for Romanian break Turkish? Pre-registered predictions (written before any run): (1) without a rule, Turkish replies keep &#x015F;; (2) task 7's rule makes some models write Turkish with the Romanian comma letter; (3) the scoped rule keeps Turkish intact and still fixes Romanian.
#
# **Scoring:** a Turkish reply passes when its Turkish words contain the Turkish &#x015F; and never the comma-below &#x0219; (Romanian place names such as Bra&#x0219;ov are left out of the count: either spelling is defensible there); a Romanian reply passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate over all 36 items. Every check is done on Unicode code points after NFC normalization. No LLM judge.
#
# This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
# data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

# %%
import hashlib
import json
import os
import subprocess
import sys

import pandas as pd
import kaggle_benchmarks as kbench

os.environ.setdefault("RENDER_SUBRUNS", "False")

# %%
# ---- scoring helpers (identical in every Comma Below task) ----
# Scoring helpers. This file is pasted verbatim into every generated task, so
# it must stay ASCII-only and depend on the standard library only.
import json
import re
import unicodedata

COMMA_LETTERS = "".join(map(chr, (0x218, 0x219, 0x21A, 0x21B)))  # comma below: S s T t
CEDILLA_LETTERS = "".join(map(chr, (0x15E, 0x15F, 0x162, 0x163)))  # cedilla (wrong for Romanian)
# a with caron / a with tilde, sometimes used instead of a with breve
OTHER_LOOKALIKES = "".join(map(chr, (0x1CD, 0x1CE, 0xC3, 0xE3)))

_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


_THINK = re.compile(r"<think>.*?</think>", re.S | re.I)


def visible(text):
    """The part of an answer a user would see: drop <think>...</think> reasoning.

    Some models return their reasoning inline. An unclosed <think> means the
    answer never started, so everything from the tag on is dropped.
    """
    t = _THINK.sub("", text or "")
    k = t.lower().find("<think>")
    return (t[:k] if k >= 0 else t).strip()


def unescape(text):
    """Decode JSON/JS style \\uXXXX escapes so escaped letters are scored too."""
    return _ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text or "")


def nfc(text):
    return unicodedata.normalize("NFC", text or "")


def census(text):
    """Count Romanian s/t letters by encoding after NFC.

    NFC folds s + U+0326 into the comma letter and s + U+0327 into the
    cedilla letter, so decomposed output is judged by what it renders as.
    """
    t = nfc(unescape(text))
    return {
        "comma": sum(t.count(c) for c in COMMA_LETTERS),
        "cedilla": sum(t.count(c) for c in CEDILLA_LETTERS),
        "lookalike": sum(t.count(c) for c in OTHER_LOOKALIKES),
        "chars": len(t),
    }


def fold(text):
    """Case-insensitive but code-point exact: casefold keeps comma vs cedilla apart."""
    return nfc(unescape(text)).casefold()


def missing_required(text, required):
    hay = fold(text)
    return [w for w in required if fold(w) not in hay]


QUOTES_OPEN = "\"'" + "".join(map(chr, (0x201E, 0x201C, 0xAB)))
QUOTES_CLOSE = "\"'" + "".join(map(chr, (0x201D, 0xBB)))

_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)


def words(text):
    return _WORD.findall(nfc(text))


def st_words(text):
    """Distinct words (casefolded) that contain a comma-below s/t."""
    return sorted({w.casefold() for w in words(text) if any(c in w for c in COMMA_LETTERS)})


def strip_wrapping(text):
    """Remove code fences, surrounding quotes and whitespace from a one-line answer."""
    t = (text or "").strip()
    t = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", t).strip()
    if len(t) >= 2 and t[0] in QUOTES_OPEN and t[-1] in QUOTES_CLOSE:
        t = t[1:-1].strip()
    return t


def restore_score(output, gold):
    """Word-level comparison of a restored sentence with its gold.

    Returns (exact, word_accuracy). Punctuation and case are ignored; letters
    are compared code point by code point.
    """
    out_words = [w.casefold() for w in words(strip_wrapping(output).splitlines()[0] if output and output.strip() else "")]
    gold_words = [w.casefold() for w in words(gold)]
    if not gold_words:
        return False, 0.0
    if len(out_words) != len(gold_words):
        # Align greedily so one inserted/dropped word does not zero the item.
        import difflib

        sm = difflib.SequenceMatcher(a=gold_words, b=out_words, autojunk=False)
        matched = sum(block.size for block in sm.get_matching_blocks())
        return False, matched / len(gold_words)
    hits = sum(a == b for a, b in zip(gold_words, out_words))
    return hits == len(gold_words), hits / len(gold_words)


def main_text(output, gold):
    """The paragraph of an answer that is the rewritten text.

    Models sometimes add a changelog ("X -> Y") that quotes the old letters.
    The paragraph most similar to the gold is the text the user asked for;
    the rest is returned separately so it can be reported, not scored.
    """
    import difflib

    paras = [p.strip() for p in re.split(r"\n\s*\n", output or "") if p.strip()]
    if not paras:
        return "", ""
    g = fold(gold)
    best = max(paras, key=lambda p: difflib.SequenceMatcher(a=g, b=fold(p), autojunk=False).ratio())
    rest = "\n\n".join(p for p in paras if p is not best)
    return best, rest


def parse_bool(text):
    t = (text or "").strip().lower()
    m = re.search(r"\b(true|false|yes|no)\b", t)
    if not m:
        return None
    return m.group(1) in ("true", "yes")


def parse_codepoint(text):
    m = re.search(r"U\+([0-9A-Fa-f]{4,6})", text or "")
    return ("U+" + m.group(1).upper().rjust(4, "0")) if m else None


def extract_python(text):
    """First fenced python block, else first fenced block, else the text."""
    t = text or ""
    m = re.search(r"```(?:python|py)\s*\n(.*?)```", t, re.S)
    if not m:
        m = re.search(r"```[a-zA-Z]*\s*\n(.*?)```", t, re.S)
    return (m.group(1) if m else t).strip()


def dumps(obj):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True)

# %%
# ---- data ----
ITEMS = [
    {'item_id': 'TR01-none', 'base_id': 'TR01', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'Merhaba, \xf6n\xfcm\xfczdeki cuma ve cumartesi i\xe7in iki ki\u015filik bir oda ay\u0131rtmak istiyorum. Kahvalt\u0131 fiyata dahil mi? \u015eimdiden te\u015fekk\xfcr ederim.'},
    {'item_id': 'TR01-rule', 'base_id': 'TR01', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Merhaba, \xf6n\xfcm\xfczdeki cuma ve cumartesi i\xe7in iki ki\u015filik bir oda ay\u0131rtmak istiyorum. Kahvalt\u0131 fiyata dahil mi? \u015eimdiden te\u015fekk\xfcr ederim.'},
    {'item_id': 'TR01-scoped', 'base_id': 'TR01', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Merhaba, \xf6n\xfcm\xfczdeki cuma ve cumartesi i\xe7in iki ki\u015filik bir oda ay\u0131rtmak istiyorum. Kahvalt\u0131 fiyata dahil mi? \u015eimdiden te\u015fekk\xfcr ederim.'},
    {'item_id': 'TR02-none', 'base_id': 'TR02', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': '\u0130yi ak\u015famlar, cumartesi gecesi saat on bir gibi varaca\u011f\u0131z. Bu kadar ge\xe7 giri\u015f yapmak m\xfcmk\xfcn m\xfc? D\xf6rt ki\u015fiyiz ve k\xfc\xe7\xfck bir k\xf6pe\u011fimiz var.'},
    {'item_id': 'TR02-rule', 'base_id': 'TR02', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': '\u0130yi ak\u015famlar, cumartesi gecesi saat on bir gibi varaca\u011f\u0131z. Bu kadar ge\xe7 giri\u015f yapmak m\xfcmk\xfcn m\xfc? D\xf6rt ki\u015fiyiz ve k\xfc\xe7\xfck bir k\xf6pe\u011fimiz var.'},
    {'item_id': 'TR02-scoped', 'base_id': 'TR02', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': '\u0130yi ak\u015famlar, cumartesi gecesi saat on bir gibi varaca\u011f\u0131z. Bu kadar ge\xe7 giri\u015f yapmak m\xfcmk\xfcn m\xfc? D\xf6rt ki\u015fiyiz ve k\xfc\xe7\xfck bir k\xf6pe\u011fimiz var.'},
    {'item_id': 'TR03-none', 'base_id': 'TR03', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'Merhaba, gelecek haftaki rezervasyonumu iptal etmek istiyorum \xe7\xfcnk\xfc k\u0131z\u0131m hastaland\u0131. \xd6dedi\u011fim kaporay\u0131 geri alabilir miyim? \xc7ok te\u015fekk\xfcrler.'},
    {'item_id': 'TR03-rule', 'base_id': 'TR03', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Merhaba, gelecek haftaki rezervasyonumu iptal etmek istiyorum \xe7\xfcnk\xfc k\u0131z\u0131m hastaland\u0131. \xd6dedi\u011fim kaporay\u0131 geri alabilir miyim? \xc7ok te\u015fekk\xfcrler.'},
    {'item_id': 'TR03-scoped', 'base_id': 'TR03', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Merhaba, gelecek haftaki rezervasyonumu iptal etmek istiyorum \xe7\xfcnk\xfc k\u0131z\u0131m hastaland\u0131. \xd6dedi\u011fim kaporay\u0131 geri alabilir miyim? \xc7ok te\u015fekk\xfcrler.'},
    {'item_id': 'TR04-none', 'base_id': 'TR04', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'Selam! Pansiyondan \u015fehir merkezine y\xfcr\xfcyerek ka\xe7 dakika s\xfcr\xfcyor? Ak\u015famlar\u0131 otob\xfcs var m\u0131, yoksa taksi mi \xe7a\u011f\u0131rmal\u0131y\u0131z?'},
    {'item_id': 'TR04-rule', 'base_id': 'TR04', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Selam! Pansiyondan \u015fehir merkezine y\xfcr\xfcyerek ka\xe7 dakika s\xfcr\xfcyor? Ak\u015famlar\u0131 otob\xfcs var m\u0131, yoksa taksi mi \xe7a\u011f\u0131rmal\u0131y\u0131z?'},
    {'item_id': 'TR04-scoped', 'base_id': 'TR04', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Selam! Pansiyondan \u015fehir merkezine y\xfcr\xfcyerek ka\xe7 dakika s\xfcr\xfcyor? Ak\u015famlar\u0131 otob\xfcs var m\u0131, yoksa taksi mi \xe7a\u011f\u0131rmal\u0131y\u0131z?'},
    {'item_id': 'TR05-none', 'base_id': 'TR05', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': '\u0130yi g\xfcnler, ge\xe7en hafta sonu sizde kald\u0131m ve telefon \u015farj aletimi odada unuttu\u011fumu d\xfc\u015f\xfcn\xfcyorum. Kontrol edebilir misiniz l\xfctfen?'},
    {'item_id': 'TR05-rule', 'base_id': 'TR05', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': '\u0130yi g\xfcnler, ge\xe7en hafta sonu sizde kald\u0131m ve telefon \u015farj aletimi odada unuttu\u011fumu d\xfc\u015f\xfcn\xfcyorum. Kontrol edebilir misiniz l\xfctfen?'},
    {'item_id': 'TR05-scoped', 'base_id': 'TR05', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': '\u0130yi g\xfcnler, ge\xe7en hafta sonu sizde kald\u0131m ve telefon \u015farj aletimi odada unuttu\u011fumu d\xfc\u015f\xfcn\xfcyorum. Kontrol edebilir misiniz l\xfctfen?'},
    {'item_id': 'TR06-none', 'base_id': 'TR06', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'Merhaba, ekim ay\u0131nda otuz ki\u015filik bir aile bulu\u015fmas\u0131 d\xfczenliyoruz. Salonunuz ve geleneksel yemeklerden olu\u015fan bir men\xfcn\xfcz var m\u0131?'},
    {'item_id': 'TR06-rule', 'base_id': 'TR06', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Merhaba, ekim ay\u0131nda otuz ki\u015filik bir aile bulu\u015fmas\u0131 d\xfczenliyoruz. Salonunuz ve geleneksel yemeklerden olu\u015fan bir men\xfcn\xfcz var m\u0131?'},
    {'item_id': 'TR06-scoped', 'base_id': 'TR06', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Merhaba, ekim ay\u0131nda otuz ki\u015filik bir aile bulu\u015fmas\u0131 d\xfczenliyoruz. Salonunuz ve geleneksel yemeklerden olu\u015fan bir men\xfcn\xfcz var m\u0131?'},
    {'item_id': 'TR07-none', 'base_id': 'TR07', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'Merhaba, e\u015fimle birlikte balay\u0131 i\xe7in \xfc\xe7 gece kalmak istiyoruz. Manzaral\u0131 ve sessiz bir odan\u0131z var m\u0131? Bir de yak\u0131nlarda \u015farap tad\u0131m\u0131 yap\u0131labilecek bir yer \xf6nerir misiniz?'},
    {'item_id': 'TR07-rule', 'base_id': 'TR07', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Merhaba, e\u015fimle birlikte balay\u0131 i\xe7in \xfc\xe7 gece kalmak istiyoruz. Manzaral\u0131 ve sessiz bir odan\u0131z var m\u0131? Bir de yak\u0131nlarda \u015farap tad\u0131m\u0131 yap\u0131labilecek bir yer \xf6nerir misiniz?'},
    {'item_id': 'TR07-scoped', 'base_id': 'TR07', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Merhaba, e\u015fimle birlikte balay\u0131 i\xe7in \xfc\xe7 gece kalmak istiyoruz. Manzaral\u0131 ve sessiz bir odan\u0131z var m\u0131? Bir de yak\u0131nlarda \u015farap tad\u0131m\u0131 yap\u0131labilecek bir yer \xf6nerir misiniz?'},
    {'item_id': 'TR08-none', 'base_id': 'TR08', 'lang': 'tr', 'rule': 'none', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences.", 'prompt': 'G\xfcnayd\u0131n, odada \xe7al\u0131\u015fma masas\u0131 ve h\u0131zl\u0131 internet var m\u0131? \u0130\u015f i\xe7in geliyorum ve her g\xfcn \xe7evrim i\xe7i toplant\u0131lar\u0131m olacak.'},
    {'item_id': 'TR08-rule', 'base_id': 'TR08', 'lang': 'tr', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'G\xfcnayd\u0131n, odada \xe7al\u0131\u015fma masas\u0131 ve h\u0131zl\u0131 internet var m\u0131? \u0130\u015f i\xe7in geliyorum ve her g\xfcn \xe7evrim i\xe7i toplant\u0131lar\u0131m olacak.'},
    {'item_id': 'TR08-scoped', 'base_id': 'TR08', 'lang': 'tr', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'G\xfcnayd\u0131n, odada \xe7al\u0131\u015fma masas\u0131 ve h\u0131zl\u0131 internet var m\u0131? \u0130\u015f i\xe7in geliyorum ve her g\xfcn \xe7evrim i\xe7i toplant\u0131lar\u0131m olacak.'},
    {'item_id': 'E01-ro-rule', 'base_id': 'E01', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Bun\u0103 ziua! A\u015f dori s\u0103 rezerv o camer\u0103 dubl\u0103 \xeen Bra\u015fov pentru dou\u0103 nop\u0163i, de vineri p\xe2n\u0103 duminic\u0103. Ave\u0163i parcare \u015fi mic dejun inclus? Mul\u0163umesc!'},
    {'item_id': 'E01-ro-scoped', 'base_id': 'E01', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Bun\u0103 ziua! A\u015f dori s\u0103 rezerv o camer\u0103 dubl\u0103 \xeen Bra\u015fov pentru dou\u0103 nop\u0163i, de vineri p\xe2n\u0103 duminic\u0103. Ave\u0163i parcare \u015fi mic dejun inclus? Mul\u0163umesc!'},
    {'item_id': 'E02-ro-rule', 'base_id': 'E02', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Salut, ajungem \xeen Bra\u015fov s\xe2mb\u0103t\u0103 seara, pe la ora nou\u0103. Se poate face check-in \u015fi dup\u0103 ora zece? Suntem patru persoane \u015fi avem un c\xe2ine mic.'},
    {'item_id': 'E02-ro-scoped', 'base_id': 'E02', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Salut, ajungem \xeen Bra\u015fov s\xe2mb\u0103t\u0103 seara, pe la ora nou\u0103. Se poate face check-in \u015fi dup\u0103 ora zece? Suntem patru persoane \u015fi avem un c\xe2ine mic.'},
    {'item_id': 'E03-ro-rule', 'base_id': 'E03', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Bun\u0103 seara. Vreau s\u0103 anulez rezervarea de s\u0103pt\u0103m\xe2na viitoare, pentru c\u0103 mi s-a \xeemboln\u0103vit fiica. \xcemi returna\u0163i avansul? Mul\u0163umesc frumos.'},
    {'item_id': 'E03-ro-scoped', 'base_id': 'E03', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Bun\u0103 seara. Vreau s\u0103 anulez rezervarea de s\u0103pt\u0103m\xe2na viitoare, pentru c\u0103 mi s-a \xeemboln\u0103vit fiica. \xcemi returna\u0163i avansul? Mul\u0163umesc frumos.'},
    {'item_id': 'E04-ro-rule', 'base_id': 'E04', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Bun\u0103! C\xe2\u0163i kilometri sunt de la pensiune p\xe2n\u0103 la Cetatea R\xe2\u015fnov \u015fi la Castelul Bran? Exist\u0103 autobuz sau e mai bine cu ma\u015fina?'},
    {'item_id': 'E04-ro-scoped', 'base_id': 'E04', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Bun\u0103! C\xe2\u0163i kilometri sunt de la pensiune p\xe2n\u0103 la Cetatea R\xe2\u015fnov \u015fi la Castelul Bran? Exist\u0103 autobuz sau e mai bine cu ma\u015fina?'},
    {'item_id': 'E05-ro-rule', 'base_id': 'E05', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Bun\u0103 ziua, am stat la dumneavoastr\u0103 weekendul trecut \u015fi cred c\u0103 mi-am uitat \xeenc\u0103rc\u0103torul de telefon \xeen camer\u0103. Pute\u0163i verifica, v\u0103 rog?'},
    {'item_id': 'E05-ro-scoped', 'base_id': 'E05', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Bun\u0103 ziua, am stat la dumneavoastr\u0103 weekendul trecut \u015fi cred c\u0103 mi-am uitat \xeenc\u0103rc\u0103torul de telefon \xeen camer\u0103. Pute\u0163i verifica, v\u0103 rog?'},
    {'item_id': 'E06-ro-rule', 'base_id': 'E06', 'lang': 'ro', 'rule': 'rule', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.", 'prompt': 'Salutare! Organiz\u0103m o \xeent\xe2lnire de familie de treizeci de persoane \xeen octombrie. Ave\u0163i o sal\u0103 \u015fi un meniu cu m\xe2ncare tradi\u0163ional\u0103?'},
    {'item_id': 'E06-ro-scoped', 'base_id': 'E06', 'lang': 'ro', 'rule': 'scoped', 'system': "You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in the language of the guest's message, in 2 to 4 sentences. When you write Romanian, use correct Romanian orthography: \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them. This applies to Romanian only; other languages keep their own letters.", 'prompt': 'Salutare! Organiz\u0103m o \xeent\xe2lnire de familie de treizeci de persoane \xeen octombrie. Ave\u0163i o sal\u0103 \u015fi un meniu cu m\xe2ncare tradi\u0163ional\u0103?'},
]

DATA_SHA256 = "9e2a14dbe6233fda76d4a42b74386a8a1246c89ee1241a1d005513785735526f"
_blob = json.dumps(ITEMS, ensure_ascii=False, sort_keys=True).encode("utf-8")
assert hashlib.sha256(_blob).hexdigest() == DATA_SHA256, "task data was altered or re-encoded"
print("data ok:", DATA_SHA256[:12])


def save_rows(task_slug, llm, rows, errors):
    """Write every item's response and metrics next to the run file."""
    name = str(getattr(llm, "name", "model")).replace("/", "_").replace("@", "_")
    path = f"{task_slug}__{name}.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(dumps(r) + "\n")
        for e in errors:
            fh.write(dumps({"error": e}) + "\n")
    print("saved", path, len(rows), "rows,", len(errors), "errors")


BACKOFF = 15  # seconds; doubled per retry, capped at 180
TRANSIENT = ("429", "rate", "Rate", "overload", "heavy load", "500", "502", "503", "504",
             "UNAVAILABLE", "RESOURCE_EXHAUSTED", "imeout", "temporarily", "Connection",
             "available quota")


MAX_OUT = 8192  # output-token cap: Kaggle reserves quota per call from this number
CAP_PARAM_NAMES = ("max_completion_tokens", "max_tokens", None)  # tried in order on the OpenAI path


def ask(llm, text, tries=6):
    """llm.prompt with an output-token cap and backoff on transient provider errors.

    Nested evaluate() runs ignore max_attempts, so retries happen here. A retry
    calls respond() on the same chat, so the question is not sent twice. If a
    provider rejects the cap parameter's name, the next name is tried.
    """
    import time

    genai = type(llm).__name__ == "GoogleGenAI"
    names = ("max_output_tokens", None) if genai else CAP_PARAM_NAMES
    name_idx = 0
    sent = False
    attempt = 0
    while True:
        cap = {names[name_idx]: MAX_OUT} if names[name_idx] else {}
        try:
            if not sent:
                sent = True
                return visible(llm.prompt(text, extra_api_params=cap or None))
            temperature = 0 if getattr(llm, "support_temperature", False) else None
            return visible(llm.respond(seed=0, temperature=temperature, **cap).content)
        except Exception as e:  # noqa: BLE001
            msg = repr(e)
            if names[name_idx] and names[name_idx] in msg and name_idx + 1 < len(names):
                name_idx += 1  # this provider does not accept that parameter name
                continue
            attempt += 1
            if attempt >= tries or not any(k in msg for k in TRANSIENT):
                raise
            time.sleep(min(BACKOFF * 2 ** attempt, 180))


def run_items(item_task, llm, df):
    runs = item_task.evaluate(
        llm=[llm], evaluation_data=df, n_jobs=2, timeout=1800,
        on_failure="continue", remove_run_files=True,
    )
    rows = [r.result for r in runs.completed_runs if isinstance(r.result, dict)]
    errors = [
        {"item_id": r.params.get("item_id"), "message": (r.error_message or "")[-1500:]}
        for r in runs.errored_runs
    ]
    if errors:
        print(len(errors), "items errored; last error:", errors[-1]["message"][-600:])
    return rows, errors

# %%
S_CEDILLA = (chr(0x15E), chr(0x15F))
S_COMMA = (chr(0x218), chr(0x219))
TURKISH_ONLY = "".join(map(chr, (0x11F, 0x11E, 0x131, 0x130)))  # g with breve, dotless i, dotted I
_FOLD = str.maketrans({0x103: "a", 0x102: "A", 0xE2: "a", 0xC2: "A", 0xEE: "i", 0xCE: "I",
                       0x219: "s", 0x218: "S", 0x21B: "t", 0x21A: "T", 0x15F: "s", 0x15E: "S",
                       0x163: "t", 0x162: "T"})
# Romanian place names a Turkish reply may quote: either s letter is defensible inside them.
RO_NAMES = ("brasov", "rasnov", "timisoara", "iasi", "bucuresti", "sighisoara", "mures", "arges",
            "constanta", "pitesti", "cismigiu", "transfagarasan", "romania")


def turkish_counts(text):
    """(cedilla s, comma s, comma s inside Romanian names) over the words of a reply."""
    ced = com = names = 0
    for w in words(text):
        k = nfc(w).translate(_FOLD).casefold()
        n_com = sum(w.count(ch) for ch in S_COMMA)
        if any(k.startswith(n) for n in RO_NAMES):
            names += n_com
            continue
        ced += sum(w.count(ch) for ch in S_CEDILLA)
        com += n_com
    return ced, com, names


@kbench.task(name="Comma Below Turkish Item", store_task=False)
def turkish_item(llm, item_id: str, base_id: str, lang: str, rule: str, system: str, prompt: str) -> dict:
    kbench.system.send(system)
    response = ask(llm, prompt)
    t = nfc(unescape(response))
    s_ced, s_com, s_com_names = turkish_counts(t)
    c = census(response)
    if lang == "tr":
        ok = s_com == 0 and s_ced > 0
    else:
        ok = c["cedilla"] == 0 and c["lookalike"] == 0 and c["comma"] > 0
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: right s letter for the language ({lang})")
    return {"item_id": item_id, "base_id": base_id, "lang": lang, "rule": rule, "pass": ok,
            "s_cedilla": s_ced, "s_comma": s_com, "s_comma_in_names": s_com_names,
            "turkish_only": sum(t.count(ch) for ch in TURKISH_ONLY), "response": response, **c}


@kbench.task(name="Romanian Comma Below 10: Turkish Guests",
             description="Does a never-write-cedilla rule for Romanian break Turkish, where the cedilla s is correct?")
def romanian_comma_below_10_turkish_guests(llm) -> float:
    rows, errors = run_items(turkish_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-10-turkish-guests", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby(["lang", "rule"])[["pass", "s_cedilla", "s_comma"]].mean().to_string())
    return float(df["pass"].mean())

# %%
romanian_comma_below_10_turkish_guests.run(kbench.llm)

# %%
%choose romanian_comma_below_10_turkish_guests
