# %% [markdown]
# # Romanian Comma Below 3: Fix
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** six Romanian texts typed with cedilla letters, each with one ordinary typo, and three instructions: a plain *proofread*, *correct the spelling and the diacritics*, and an explicit description of the cedilla problem. Does the model repair the letters, and does it need to be told?
#
# **Scoring:** the rewritten text (the paragraph closest to the answer key; a changelog after it is ignored) passes when it has zero cedilla or look-alike letters and contains every gold word that has a comma-below letter. The typo fix is recorded separately. Score = share of answers passed. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
    {'item_id': 'F01-L1_proofread', 'base_id': 'F01', 'level': 'L1_proofread', 'text': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u0163a Sfatului, \xeen centrul istoric al Bra\u015fovului. Toate camerele au baie proprie, iar micul dejun estte inclus \xeen pre\u0163.', 'gold': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u021ba Sfatului, \xeen centrul istoric al Bra\u0219ovului. Toate camerele au baie proprie, iar micul dejun este inclus \xeen pre\u021b.', 'correct_word': 'este inclus', 'typo_word': 'estte inclus'},
    {'item_id': 'F01-L2_diacritics', 'base_id': 'F01', 'level': 'L2_diacritics', 'text': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u0163a Sfatului, \xeen centrul istoric al Bra\u015fovului. Toate camerele au baie proprie, iar micul dejun estte inclus \xeen pre\u0163.', 'gold': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u021ba Sfatului, \xeen centrul istoric al Bra\u0219ovului. Toate camerele au baie proprie, iar micul dejun este inclus \xeen pre\u021b.', 'correct_word': 'este inclus', 'typo_word': 'estte inclus'},
    {'item_id': 'F01-L3_explicit', 'base_id': 'F01', 'level': 'L3_explicit', 'text': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u0163a Sfatului, \xeen centrul istoric al Bra\u015fovului. Toate camerele au baie proprie, iar micul dejun estte inclus \xeen pre\u0163.', 'gold': 'Pensiunea noastr\u0103 se afl\u0103 la cinci minute de Pia\u021ba Sfatului, \xeen centrul istoric al Bra\u0219ovului. Toate camerele au baie proprie, iar micul dejun este inclus \xeen pre\u021b.', 'correct_word': 'este inclus', 'typo_word': 'estte inclus'},
    {'item_id': 'F02-L1_proofread', 'base_id': 'F02', 'level': 'L1_proofread', 'text': 'V\u0103 mul\u0163umim pentru rezervrae! Check-in-ul se face \xeentre orele paisprezece \u015fi dou\u0103zeci \u015fi dou\u0103. Dac\u0103 ajunge\u0163i mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u0163a\u0163i telefonic.', 'gold': 'V\u0103 mul\u021bumim pentru rezervare! Check-in-ul se face \xeentre orele paisprezece \u0219i dou\u0103zeci \u0219i dou\u0103. Dac\u0103 ajunge\u021bi mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u021ba\u021bi telefonic.', 'correct_word': 'rezervare', 'typo_word': 'rezervrae'},
    {'item_id': 'F02-L2_diacritics', 'base_id': 'F02', 'level': 'L2_diacritics', 'text': 'V\u0103 mul\u0163umim pentru rezervrae! Check-in-ul se face \xeentre orele paisprezece \u015fi dou\u0103zeci \u015fi dou\u0103. Dac\u0103 ajunge\u0163i mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u0163a\u0163i telefonic.', 'gold': 'V\u0103 mul\u021bumim pentru rezervare! Check-in-ul se face \xeentre orele paisprezece \u0219i dou\u0103zeci \u0219i dou\u0103. Dac\u0103 ajunge\u021bi mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u021ba\u021bi telefonic.', 'correct_word': 'rezervare', 'typo_word': 'rezervrae'},
    {'item_id': 'F02-L3_explicit', 'base_id': 'F02', 'level': 'L3_explicit', 'text': 'V\u0103 mul\u0163umim pentru rezervrae! Check-in-ul se face \xeentre orele paisprezece \u015fi dou\u0103zeci \u015fi dou\u0103. Dac\u0103 ajunge\u0163i mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u0163a\u0163i telefonic.', 'gold': 'V\u0103 mul\u021bumim pentru rezervare! Check-in-ul se face \xeentre orele paisprezece \u0219i dou\u0103zeci \u0219i dou\u0103. Dac\u0103 ajunge\u021bi mai t\xe2rziu, v\u0103 rug\u0103m s\u0103 ne anun\u021ba\u021bi telefonic.', 'correct_word': 'rezervare', 'typo_word': 'rezervrae'},
    {'item_id': 'F03-L1_proofread', 'base_id': 'F03', 'level': 'L1_proofread', 'text': 'Cetatea R\xe2\u015fnov a fost construit\u0103 de cavalerii teutoni \u015fi a fost restauart\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u0162ara B\xe2rsei.', 'gold': 'Cetatea R\xe2\u0219nov a fost construit\u0103 de cavalerii teutoni \u0219i a fost restaurat\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u021aara B\xe2rsei.', 'correct_word': 'restaurat\u0103', 'typo_word': 'restauart\u0103'},
    {'item_id': 'F03-L2_diacritics', 'base_id': 'F03', 'level': 'L2_diacritics', 'text': 'Cetatea R\xe2\u015fnov a fost construit\u0103 de cavalerii teutoni \u015fi a fost restauart\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u0162ara B\xe2rsei.', 'gold': 'Cetatea R\xe2\u0219nov a fost construit\u0103 de cavalerii teutoni \u0219i a fost restaurat\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u021aara B\xe2rsei.', 'correct_word': 'restaurat\u0103', 'typo_word': 'restauart\u0103'},
    {'item_id': 'F03-L3_explicit', 'base_id': 'F03', 'level': 'L3_explicit', 'text': 'Cetatea R\xe2\u015fnov a fost construit\u0103 de cavalerii teutoni \u015fi a fost restauart\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u0162ara B\xe2rsei.', 'gold': 'Cetatea R\xe2\u0219nov a fost construit\u0103 de cavalerii teutoni \u0219i a fost restaurat\u0103 \xeen ultimii ani. De acolo se vede toat\u0103 \u021aara B\xe2rsei.', 'correct_word': 'restaurat\u0103', 'typo_word': 'restauart\u0103'},
    {'item_id': 'F04-L1_proofread', 'base_id': 'F04', 'level': 'L1_proofread', 'text': '\u015ecoala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u015fi dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierle se fac p\xe2n\u0103 la sf\xe2r\u015fitul lunii iunie.', 'gold': '\u0218coala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u0219i dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierile se fac p\xe2n\u0103 la sf\xe2r\u0219itul lunii iunie.', 'correct_word': '\xcenscrierile', 'typo_word': '\xcenscrierle'},
    {'item_id': 'F04-L2_diacritics', 'base_id': 'F04', 'level': 'L2_diacritics', 'text': '\u015ecoala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u015fi dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierle se fac p\xe2n\u0103 la sf\xe2r\u015fitul lunii iunie.', 'gold': '\u0218coala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u0219i dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierile se fac p\xe2n\u0103 la sf\xe2r\u0219itul lunii iunie.', 'correct_word': '\xcenscrierile', 'typo_word': '\xcenscrierle'},
    {'item_id': 'F04-L3_explicit', 'base_id': 'F04', 'level': 'L3_explicit', 'text': '\u015ecoala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u015fi dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierle se fac p\xe2n\u0103 la sf\xe2r\u015fitul lunii iunie.', 'gold': '\u0218coala de var\u0103 pentru copii \xeencepe pe \xeent\xe2i iulie \u0219i dureaz\u0103 dou\u0103 s\u0103pt\u0103m\xe2ni. \xcenscrierile se fac p\xe2n\u0103 la sf\xe2r\u0219itul lunii iunie.', 'correct_word': '\xcenscrierile', 'typo_word': '\xcenscrierle'},
    {'item_id': 'F05-L1_proofread', 'base_id': 'F05', 'level': 'L1_proofread', 'text': '\u015etirile de ast\u0103zi: trenul spre Timi\u015foara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u015fti este aglomrat\u0103.', 'gold': '\u0218tirile de ast\u0103zi: trenul spre Timi\u0219oara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u0219ti este aglomerat\u0103.', 'correct_word': 'aglomerat\u0103', 'typo_word': 'aglomrat\u0103'},
    {'item_id': 'F05-L2_diacritics', 'base_id': 'F05', 'level': 'L2_diacritics', 'text': '\u015etirile de ast\u0103zi: trenul spre Timi\u015foara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u015fti este aglomrat\u0103.', 'gold': '\u0218tirile de ast\u0103zi: trenul spre Timi\u0219oara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u0219ti este aglomerat\u0103.', 'correct_word': 'aglomerat\u0103', 'typo_word': 'aglomrat\u0103'},
    {'item_id': 'F05-L3_explicit', 'base_id': 'F05', 'level': 'L3_explicit', 'text': '\u015etirile de ast\u0103zi: trenul spre Timi\u015foara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u015fti este aglomrat\u0103.', 'gold': '\u0218tirile de ast\u0103zi: trenul spre Timi\u0219oara \xeent\xe2rzie patruzeci de minute, iar autostrada spre Pite\u0219ti este aglomerat\u0103.', 'correct_word': 'aglomerat\u0103', 'typo_word': 'aglomrat\u0103'},
    {'item_id': 'F06-L1_proofread', 'base_id': 'F06', 'level': 'L1_proofread', 'text': 'Mul\u0163umesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u015fierele \u015fi facutra pentru luna trecut\u0103.', 'gold': 'Mul\u021bumesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u0219ierele \u0219i factura pentru luna trecut\u0103.', 'correct_word': 'factura', 'typo_word': 'facutra'},
    {'item_id': 'F06-L2_diacritics', 'base_id': 'F06', 'level': 'L2_diacritics', 'text': 'Mul\u0163umesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u015fierele \u015fi facutra pentru luna trecut\u0103.', 'gold': 'Mul\u021bumesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u0219ierele \u0219i factura pentru luna trecut\u0103.', 'correct_word': 'factura', 'typo_word': 'facutra'},
    {'item_id': 'F06-L3_explicit', 'base_id': 'F06', 'level': 'L3_explicit', 'text': 'Mul\u0163umesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u015fierele \u015fi facutra pentru luna trecut\u0103.', 'gold': 'Mul\u021bumesc pentru ajutor! M\xe2ine v\u0103 trimit fi\u0219ierele \u0219i factura pentru luna trecut\u0103.', 'correct_word': 'factura', 'typo_word': 'facutra'},
]

DATA_SHA256 = "ed9298b4f95f937b5aed97040daea250e833f5bddc44b53f8e57a11e6cea848c"
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
LEVELS = {'L1_proofread': 'Proofread the following Romanian text. Return only the corrected text.\n\n', 'L2_diacritics': 'Correct the spelling and the diacritics in the following Romanian text. Return only the corrected text.\n\n', 'L3_explicit': 'The following Romanian text was typed on an old keyboard layout that produces the cedilla letters \u015f and \u0163 instead of the correct Romanian comma-below letters \u0219 and \u021b. Return the text with every diacritic corrected, and nothing else.\n\n'}


@kbench.task(name="Comma Below Fix Item", store_task=False)
def fix_item(llm, item_id: str, base_id: str, level: str, text: str, gold: str,
             correct_word: str, typo_word: str) -> dict:
    response = ask(llm, LEVELS[level] + text)
    body, extra = main_text(response, gold)
    c = census(body)
    have = {w.casefold() for w in words(body)}
    missing = [w for w in st_words(gold) if w not in have]
    flat = fold(body)
    typo_fixed = fold(correct_word) in flat and fold(typo_word) not in flat
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and not missing
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: all s/t letters repaired")
    return {"item_id": item_id, "base_id": base_id, "level": level, "pass": ok,
            "typo_fixed": typo_fixed, "missing": missing, "extra_text": bool(extra),
            "extra_cedilla": census(extra)["cedilla"], "response": response, **c}


@kbench.task(name="Romanian Comma Below 3: Fix",
             description="Asked to proofread Romanian typed with cedilla letters, does the model repair them? Three instruction levels.")
def romanian_comma_below_3_fix(llm) -> float:
    rows, errors = run_items(fix_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-3-fix", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("level")[["pass", "typo_fixed", "cedilla"]].mean().to_string())
    return float(df["pass"].mean()) if len(df) else 0.0

# %%
romanian_comma_below_3_fix.run(kbench.llm)

# %%
%choose romanian_comma_below_3_fix
