# %% [markdown]
# # Romanian Comma Below 11: Other Look-Alikes
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** the Echo design outside Romanian. Six English news paragraphs with accented names (Z&#x00FC;rich, Caf&#x00E9; M&#x00FC;ller, M&#x00E1;laga) are summarized or used to answer a question, typed four ways: correctly; with Cyrillic look-alike letters (&#x0430; &#x0441; &#x0435; &#x043E; &#x0440; for a c e o p) in every word; with Cyrillic look-alikes only inside the accented names; and as mojibake in the same names (UTF-8 read as Windows-1252, *Z&#x00C3;&#x00BC;rich*), which looks broken. Pre-registered predictions (written before any run): (1) clean input stays near 100 %; (2) Cyrillic look-alikes are copied into answers far more often than mojibake, because mojibake looks broken and look-alikes do not; (3) the models that copy the Romanian cedilla most (task 8) also copy the Cyrillic look-alikes most. Version 2 note: version 1 had only the dense Cyrillic variant (about a third of all letters replaced, versus about 2 % for the Romanian cedilla). Its single run (Gemini 3.7 Flash) copied none of it, so version 2 adds look-alikes confined to the names, the same words mojibake touches. The predictions are unchanged.
#
# **Scoring:** a clean or Cyrillic-input answer passes when it contains no Cyrillic letter; a mojibake-input answer passes when it contains no mojibake marker (&#x00C3; or &#x00C2;). Score = pass rate over all 48 items. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
    {'item_id': 'L01-summary-clean', 'base_id': 'L01', 'kind': 'summary', 'variant': 'clean', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-summary-cyrillic-all', 'base_id': 'L01', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nTh\u0435 night tr\u0430in fr\u043em Z\xfcri\u0441h t\u043e M\xfcn\u0441h\u0435n will run \u0430g\u0430in fr\u043em n\u0435xt m\u043enth, \u0430ft\u0435r \u0430 tw\u043e-y\u0435\u0430r \u0440\u0430us\u0435. Th\u0435 j\u043eurn\u0435y t\u0430k\u0435s \u0430b\u043eut f\u043eur h\u043eurs, \u0430nd th\u0435 sl\u0435\u0435\u0440ing \u0441\u0430rs h\u0430v\u0435 b\u0435\u0435n r\u0435n\u043ev\u0430t\u0435d.', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-summary-cyrillic-names', 'base_id': 'L01', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe night train from Z\xfcr\u0456\u0441\u04bb to \u041c\xfcn\u0441\u04bb\u0435n will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-summary-mojibake', 'base_id': 'L01', 'kind': 'summary', 'variant': 'mojibake', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe night train from Z\xc3\xbcrich to M\xc3\xbcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-rag-clean', 'base_id': 'L01', 'kind': 'rag', 'variant': 'clean', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.\n\nQuestion: Between which two cities does the night train run, and how long is the journey?', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-rag-cyrillic-all', 'base_id': 'L01', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nTh\u0435 night tr\u0430in fr\u043em Z\xfcri\u0441h t\u043e M\xfcn\u0441h\u0435n will run \u0430g\u0430in fr\u043em n\u0435xt m\u043enth, \u0430ft\u0435r \u0430 tw\u043e-y\u0435\u0430r \u0440\u0430us\u0435. Th\u0435 j\u043eurn\u0435y t\u0430k\u0435s \u0430b\u043eut f\u043eur h\u043eurs, \u0430nd th\u0435 sl\u0435\u0435\u0440ing \u0441\u0430rs h\u0430v\u0435 b\u0435\u0435n r\u0435n\u043ev\u0430t\u0435d.\n\nQuestion: Between which two cities does the night train run, and how long is the journey?', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-rag-cyrillic-names', 'base_id': 'L01', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe night train from Z\xfcr\u0456\u0441\u04bb to \u041c\xfcn\u0441\u04bb\u0435n will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.\n\nQuestion: Between which two cities does the night train run, and how long is the journey?', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L01-rag-mojibake', 'base_id': 'L01', 'kind': 'rag', 'variant': 'mojibake', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe night train from Z\xc3\xbcrich to M\xc3\xbcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.\n\nQuestion: Between which two cities does the night train run, and how long is the journey?', 'gold': 'The night train from Z\xfcrich to M\xfcnchen will run again from next month, after a two-year pause. The journey takes about four hours, and the sleeping cars have been renovated.'},
    {'item_id': 'L02-summary-clean', 'base_id': 'L02', 'kind': 'summary', 'variant': 'clean', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nCaf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-summary-cyrillic-all', 'base_id': 'L02', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nC\u0430f\xe9 M\xfcll\u0435r in K\xf6ln will \u0441l\u043es\u0435 \u0430t th\u0435 \u0435nd \u043ef th\u0435 m\u043enth \u0430ft\u0435r nin\u0435ty y\u0435\u0430rs. Th\u0435 \u043ewn\u0435r, J\u043es\xe9 F\u0435rn\xe1nd\u0435z, s\u0430ys th\u0435 r\u0435nt h\u0430s d\u043eubl\u0435d, \u0430nd th\u0435 l\u0430st d\u0430y \u043ef s\u0435rvi\u0441\u0435 will b\u0435 \u0430 Sund\u0430y.', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-summary-cyrillic-names', 'base_id': 'L02', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\n\u0421\u0430f\xe9 \u041c\xfcll\u0435r in \u041a\xf6ln will close at the end of the month after ninety years. The owner, \u0408\u043e\u0455\xe9 F\u0435rn\xe1nd\u0435z, says the rent has doubled, and the last day of service will be a Sunday.', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-summary-mojibake', 'base_id': 'L02', 'kind': 'summary', 'variant': 'mojibake', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nCaf\xc3\xa9 M\xc3\xbcller in K\xc3\xb6ln will close at the end of the month after ninety years. The owner, Jos\xc3\xa9 Fern\xc3\xa1ndez, says the rent has doubled, and the last day of service will be a Sunday.', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-rag-clean', 'base_id': 'L02', 'kind': 'rag', 'variant': 'clean', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nCaf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.\n\nQuestion: Which caf\xe9 is closing, in which city, and who owns it?', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-rag-cyrillic-all', 'base_id': 'L02', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nC\u0430f\xe9 M\xfcll\u0435r in K\xf6ln will \u0441l\u043es\u0435 \u0430t th\u0435 \u0435nd \u043ef th\u0435 m\u043enth \u0430ft\u0435r nin\u0435ty y\u0435\u0430rs. Th\u0435 \u043ewn\u0435r, J\u043es\xe9 F\u0435rn\xe1nd\u0435z, s\u0430ys th\u0435 r\u0435nt h\u0430s d\u043eubl\u0435d, \u0430nd th\u0435 l\u0430st d\u0430y \u043ef s\u0435rvi\u0441\u0435 will b\u0435 \u0430 Sund\u0430y.\n\nQuestion: Which caf\xe9 is closing, in which city, and who owns it?', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-rag-cyrillic-names', 'base_id': 'L02', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\n\u0421\u0430f\xe9 \u041c\xfcll\u0435r in \u041a\xf6ln will close at the end of the month after ninety years. The owner, \u0408\u043e\u0455\xe9 F\u0435rn\xe1nd\u0435z, says the rent has doubled, and the last day of service will be a Sunday.\n\nQuestion: Which caf\xe9 is closing, in which city, and who owns it?', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L02-rag-mojibake', 'base_id': 'L02', 'kind': 'rag', 'variant': 'mojibake', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nCaf\xc3\xa9 M\xc3\xbcller in K\xc3\xb6ln will close at the end of the month after ninety years. The owner, Jos\xc3\xa9 Fern\xc3\xa1ndez, says the rent has doubled, and the last day of service will be a Sunday.\n\nQuestion: Which caf\xe9 is closing, in which city, and who owns it?', 'gold': 'Caf\xe9 M\xfcller in K\xf6ln will close at the end of the month after ninety years. The owner, Jos\xe9 Fern\xe1ndez, says the rent has doubled, and the last day of service will be a Sunday.'},
    {'item_id': 'L03-summary-clean', 'base_id': 'L03', 'kind': 'summary', 'variant': 'clean', 'prompt': "Summarize the following news paragraph in English, in at most two sentences.\n\nMore than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-summary-cyrillic-all', 'base_id': 'L03', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': "Summarize the following news paragraph in English, in at most two sentences.\n\nM\u043er\u0435 th\u0430n fift\u0435\u0435n th\u043eus\u0430nd \u0440\u0435\u043e\u0440l\u0435 \u0430tt\u0435nd\u0435d th\u0435 film f\u0435stiv\u0430l in G\xf6t\u0435b\u043erg \u043ev\u0435r thr\u0435\u0435 d\u0430ys. Th\u0435 \u043erg\u0430niz\u0435rs s\u0430y ti\u0441k\u0435ts f\u043er n\u0435xt y\u0435\u0430r's \u0435diti\u043en will g\u043e \u043en s\u0430l\u0435 in D\u0435\u0441\u0435mb\u0435r, with \u0430 dis\u0441\u043eunt f\u043er stud\u0435nts.", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-summary-cyrillic-names', 'base_id': 'L03', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': "Summarize the following news paragraph in English, in at most two sentences.\n\nMore than fifteen thousand people attended the film festival in G\xf6t\u0435b\u043erg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-summary-mojibake', 'base_id': 'L03', 'kind': 'summary', 'variant': 'mojibake', 'prompt': "Summarize the following news paragraph in English, in at most two sentences.\n\nMore than fifteen thousand people attended the film festival in G\xc3\xb6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-rag-clean', 'base_id': 'L03', 'kind': 'rag', 'variant': 'clean', 'prompt': "Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nMore than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.\n\nQuestion: Where did the festival take place, and when do next year's tickets go on sale?", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-rag-cyrillic-all', 'base_id': 'L03', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': "Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nM\u043er\u0435 th\u0430n fift\u0435\u0435n th\u043eus\u0430nd \u0440\u0435\u043e\u0440l\u0435 \u0430tt\u0435nd\u0435d th\u0435 film f\u0435stiv\u0430l in G\xf6t\u0435b\u043erg \u043ev\u0435r thr\u0435\u0435 d\u0430ys. Th\u0435 \u043erg\u0430niz\u0435rs s\u0430y ti\u0441k\u0435ts f\u043er n\u0435xt y\u0435\u0430r's \u0435diti\u043en will g\u043e \u043en s\u0430l\u0435 in D\u0435\u0441\u0435mb\u0435r, with \u0430 dis\u0441\u043eunt f\u043er stud\u0435nts.\n\nQuestion: Where did the festival take place, and when do next year's tickets go on sale?", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-rag-cyrillic-names', 'base_id': 'L03', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': "Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nMore than fifteen thousand people attended the film festival in G\xf6t\u0435b\u043erg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.\n\nQuestion: Where did the festival take place, and when do next year's tickets go on sale?", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L03-rag-mojibake', 'base_id': 'L03', 'kind': 'rag', 'variant': 'mojibake', 'prompt': "Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nMore than fifteen thousand people attended the film festival in G\xc3\xb6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students.\n\nQuestion: Where did the festival take place, and when do next year's tickets go on sale?", 'gold': "More than fifteen thousand people attended the film festival in G\xf6teborg over three days. The organizers say tickets for next year's edition will go on sale in December, with a discount for students."},
    {'item_id': 'L04-summary-clean', 'base_id': 'L04', 'kind': 'summary', 'variant': 'clean', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-summary-cyrillic-all', 'base_id': 'L04', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nTh\u0435 b\u0435\u0430\u0441h \u0440r\u043em\u0435n\u0430d\u0435 in M\xe1l\u0430g\u0430 is \u0441l\u043es\u0435d f\u043er r\u0435\u0440\u0430irs \u0430ft\u0435r th\u0435 st\u043erm. R\u0435sid\u0435nts \u0430r\u0435 \u0430sk\u0435d t\u043e us\u0435 th\u0435 \u0441\u0430r \u0440\u0430rks n\u0435\u0430r th\u0435 M\u0430r\xed\u0430 Z\u0430mbr\u0430n\u043e st\u0430ti\u043en until th\u0435 w\u043erk is finish\u0435d.', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-summary-cyrillic-names', 'base_id': 'L04', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe beach promenade in \u041c\xe1l\u0430g\u0430 is closed for repairs after the storm. Residents are asked to use the car parks near the \u041c\u0430r\xed\u0430 Zambrano station until the work is finished.', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-summary-mojibake', 'base_id': 'L04', 'kind': 'summary', 'variant': 'mojibake', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe beach promenade in M\xc3\xa1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xc3\xada Zambrano station until the work is finished.', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-rag-clean', 'base_id': 'L04', 'kind': 'rag', 'variant': 'clean', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.\n\nQuestion: Where are residents asked to park?', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-rag-cyrillic-all', 'base_id': 'L04', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nTh\u0435 b\u0435\u0430\u0441h \u0440r\u043em\u0435n\u0430d\u0435 in M\xe1l\u0430g\u0430 is \u0441l\u043es\u0435d f\u043er r\u0435\u0440\u0430irs \u0430ft\u0435r th\u0435 st\u043erm. R\u0435sid\u0435nts \u0430r\u0435 \u0430sk\u0435d t\u043e us\u0435 th\u0435 \u0441\u0430r \u0440\u0430rks n\u0435\u0430r th\u0435 M\u0430r\xed\u0430 Z\u0430mbr\u0430n\u043e st\u0430ti\u043en until th\u0435 w\u043erk is finish\u0435d.\n\nQuestion: Where are residents asked to park?', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-rag-cyrillic-names', 'base_id': 'L04', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe beach promenade in \u041c\xe1l\u0430g\u0430 is closed for repairs after the storm. Residents are asked to use the car parks near the \u041c\u0430r\xed\u0430 Zambrano station until the work is finished.\n\nQuestion: Where are residents asked to park?', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L04-rag-mojibake', 'base_id': 'L04', 'kind': 'rag', 'variant': 'mojibake', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe beach promenade in M\xc3\xa1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xc3\xada Zambrano station until the work is finished.\n\nQuestion: Where are residents asked to park?', 'gold': 'The beach promenade in M\xe1laga is closed for repairs after the storm. Residents are asked to use the car parks near the Mar\xeda Zambrano station until the work is finished.'},
    {'item_id': 'L05-summary-clean', 'base_id': 'L05', 'kind': 'summary', 'variant': 'clean', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-summary-cyrillic-all', 'base_id': 'L05', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nTh\u0435 r\u043e\u0430d \u043ev\u0435r th\u0435 Gr\u043e\xdfgl\u043e\u0441kn\u0435r \u0440\u0430ss \u0441l\u043es\u0435s \u0435v\u0435ry y\u0435\u0430r \u0430t th\u0435 \u0435nd \u043ef O\u0441t\u043eb\u0435r \u0430nd usu\u0430lly r\u0435\u043e\u0440\u0435ns in \u0435\u0430rly M\u0430y. Th\u0435 \u0430uth\u043eriti\u0435s \u0430dvis\u0435 driv\u0435rs t\u043e \u0441h\u0435\u0441k th\u0435 \u0441\u043enditi\u043ens b\u0435f\u043er\u0435 l\u0435\u0430ving, b\u0435\u0441\u0430us\u0435 sn\u043ew \u0441\u0430n f\u0430ll \u0430s \u0435\u0430rly \u0430s S\u0435\u0440t\u0435mb\u0435r.', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-summary-cyrillic-names', 'base_id': 'L05', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe road over the Gr\u043e\xdfgl\u043e\u0441kn\u0435r pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-summary-mojibake', 'base_id': 'L05', 'kind': 'summary', 'variant': 'mojibake', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nThe road over the Gro\xc3\u0178glockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-rag-clean', 'base_id': 'L05', 'kind': 'rag', 'variant': 'clean', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.\n\nQuestion: When does the road close, and when does it usually reopen?', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-rag-cyrillic-all', 'base_id': 'L05', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nTh\u0435 r\u043e\u0430d \u043ev\u0435r th\u0435 Gr\u043e\xdfgl\u043e\u0441kn\u0435r \u0440\u0430ss \u0441l\u043es\u0435s \u0435v\u0435ry y\u0435\u0430r \u0430t th\u0435 \u0435nd \u043ef O\u0441t\u043eb\u0435r \u0430nd usu\u0430lly r\u0435\u043e\u0440\u0435ns in \u0435\u0430rly M\u0430y. Th\u0435 \u0430uth\u043eriti\u0435s \u0430dvis\u0435 driv\u0435rs t\u043e \u0441h\u0435\u0441k th\u0435 \u0441\u043enditi\u043ens b\u0435f\u043er\u0435 l\u0435\u0430ving, b\u0435\u0441\u0430us\u0435 sn\u043ew \u0441\u0430n f\u0430ll \u0430s \u0435\u0430rly \u0430s S\u0435\u0440t\u0435mb\u0435r.\n\nQuestion: When does the road close, and when does it usually reopen?', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-rag-cyrillic-names', 'base_id': 'L05', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe road over the Gr\u043e\xdfgl\u043e\u0441kn\u0435r pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.\n\nQuestion: When does the road close, and when does it usually reopen?', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L05-rag-mojibake', 'base_id': 'L05', 'kind': 'rag', 'variant': 'mojibake', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nThe road over the Gro\xc3\u0178glockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.\n\nQuestion: When does the road close, and when does it usually reopen?', 'gold': 'The road over the Gro\xdfglockner pass closes every year at the end of October and usually reopens in early May. The authorities advise drivers to check the conditions before leaving, because snow can fall as early as September.'},
    {'item_id': 'L06-summary-clean', 'base_id': 'L06', 'kind': 'summary', 'variant': 'clean', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nSchools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-summary-cyrillic-all', 'base_id': 'L06', 'kind': 'summary', 'variant': 'cyrillic-all', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nS\u0441h\u043e\u043els in th\u0435 \u0441\u0430nt\u043en \u043ef G\u0435n\xe8v\u0435 will st\u0430rt \u0430 w\u0435\u0435k l\u0430t\u0435r th\u0430n \u0440l\u0430nn\u0435d, \u0430ft\u0435r s\u0435v\u0435r\u0430l buildings n\u0435\u0435d\u0435d r\u0435\u0440\u0430irs. P\u0430r\u0435nts will b\u0435 inf\u043erm\u0435d by \u0430 m\u0435ss\u0430g\u0435 fr\u043em \u0435\u0430\u0441h s\u0441h\u043e\u043el.', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-summary-cyrillic-names', 'base_id': 'L06', 'kind': 'summary', 'variant': 'cyrillic-names', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nSchools in the canton of G\u0435n\xe8v\u0435 will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-summary-mojibake', 'base_id': 'L06', 'kind': 'summary', 'variant': 'mojibake', 'prompt': 'Summarize the following news paragraph in English, in at most two sentences.\n\nSchools in the canton of Gen\xc3\xa8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-rag-clean', 'base_id': 'L06', 'kind': 'rag', 'variant': 'clean', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nSchools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.\n\nQuestion: Which schools will start later, and why?', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-rag-cyrillic-all', 'base_id': 'L06', 'kind': 'rag', 'variant': 'cyrillic-all', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nS\u0441h\u043e\u043els in th\u0435 \u0441\u0430nt\u043en \u043ef G\u0435n\xe8v\u0435 will st\u0430rt \u0430 w\u0435\u0435k l\u0430t\u0435r th\u0430n \u0440l\u0430nn\u0435d, \u0430ft\u0435r s\u0435v\u0435r\u0430l buildings n\u0435\u0435d\u0435d r\u0435\u0440\u0430irs. P\u0430r\u0435nts will b\u0435 inf\u043erm\u0435d by \u0430 m\u0435ss\u0430g\u0435 fr\u043em \u0435\u0430\u0441h s\u0441h\u043e\u043el.\n\nQuestion: Which schools will start later, and why?', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-rag-cyrillic-names', 'base_id': 'L06', 'kind': 'rag', 'variant': 'cyrillic-names', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nSchools in the canton of G\u0435n\xe8v\u0435 will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.\n\nQuestion: Which schools will start later, and why?', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
    {'item_id': 'L06-rag-mojibake', 'base_id': 'L06', 'kind': 'rag', 'variant': 'mojibake', 'prompt': 'Answer the question using only the text below. Answer in English, in one sentence.\n\nText:\nSchools in the canton of Gen\xc3\xa8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.\n\nQuestion: Which schools will start later, and why?', 'gold': 'Schools in the canton of Gen\xe8ve will start a week later than planned, after several buildings needed repairs. Parents will be informed by a message from each school.'},
]

DATA_SHA256 = "7c6e9d3a47b959a7d493a3ce36e8e41bab206284daf48919670c274e8cb3a109"
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
MOJIBAKE_MARKERS = (chr(0xC3), chr(0xC2))


def cyrillic_count(text):
    return sum(1 for ch in text if 0x400 <= ord(ch) <= 0x4FF)


@kbench.task(name="Comma Below Look-Alike Item", store_task=False)
def lookalike_item(llm, item_id: str, base_id: str, kind: str, variant: str, prompt: str, gold: str) -> dict:
    response = ask(llm, prompt)
    t = nfc(unescape(response))
    cyr = cyrillic_count(t)
    moji = sum(t.count(m) for m in MOJIBAKE_MARKERS)
    latin = sum(1 for ch in t if ch.isascii() and ch.isalpha())
    gold_accents = sorted({w for w in words(gold) if not w.isascii()})
    accents_kept = [w for w in gold_accents if w in t]
    ok = latin > 0 and cyr == 0 and moji == 0
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: no Cyrillic letters and no mojibake in the answer")
    return {"item_id": item_id, "base_id": base_id, "kind": kind, "variant": variant, "pass": ok,
            "cyrillic": cyr, "mojibake": moji, "accented_words": gold_accents,
            "accented_kept": accents_kept, "response": response}


@kbench.task(name="Romanian Comma Below 11: Other Look-Alikes",
             description="English text typed with Cyrillic look-alike letters or as mojibake: which errors do models copy?")
def romanian_comma_below_11_other_look_alikes(llm) -> float:
    rows, errors = run_items(lookalike_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-11-other-look-alikes", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby(["variant", "kind"])[["pass", "cyrillic", "mojibake"]].mean().to_string())
    return float(df["pass"].mean())

# %%
romanian_comma_below_11_other_look_alikes.run(kbench.llm)

# %%
%choose romanian_comma_below_11_other_look_alikes
