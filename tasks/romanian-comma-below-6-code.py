# %% [markdown]
# # Romanian Comma Below 6: Code
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** the model writes `fix_romanian(text)`, a Python function that repairs cedilla letters. Two prompt phrasings (one names every letter, one only gives the goal). Hidden tests cover lowercase and uppercase, decomposed forms (s + U+0327), text that is already correct, French &#x00E7; that must not change, whitespace and emoji, and idempotence.
#
# **Scoring:** share of the 14 hidden tests passed, averaged over the two prompts. The code runs in a subprocess with a 30 s timeout. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
DATA = {
    'prompts': [
    {'item_id': 'C1_explicit', 'prompt': "Our Romanian website's content was typed on old keyboards and uses the cedilla letters \u015f, \u015e, \u0163, \u0162 instead of the correct Romanian comma-below letters \u0219, \u0218, \u021b, \u021a. Write a Python function `fix_romanian(text: str) -> str` that repairs the text. Only change what needs changing. Reply with one Python code block containing the function (imports allowed, no tests, no explanation)."},
    {'item_id': 'C2_goal', 'prompt': "Write a Python function `fix_romanian(text: str) -> str` that normalizes the Romanian diacritics in a text so that it follows the standard Romanian orthography. For example, 'Bra\u015fov' must become 'Bra\u0219ov'. Only change what needs changing. Reply with one Python code block containing the function (imports allowed, no tests, no explanation)."},
],
    'tests': [
    ['basic', 'Bra\u015fov', 'Bra\u0219ov'],
    ['two_words', 'Timi\u015foara, Ia\u015fi', 'Timi\u0219oara, Ia\u0219i'],
    ['upper_s', '\u015eCOALA', '\u0218COALA'],
    ['upper_t', '\u0162ara B\xe2rsei', '\u021aara B\xe2rsei'],
    ['lower_t', 'mul\u0163umesc', 'mul\u021bumesc'],
    ['decomposed_s', 'Bras\u0327ov', 'Bra\u0219ov'],
    ['decomposed_T', 'T\u0327ara', '\u021aara'],
    ['already_correct', 'Bra\u0219ov \u0219i Timi\u0219oara', 'Bra\u0219ov \u0219i Timi\u0219oara'],
    ['other_letters', 'M\u0103n\u0103stirea din T\xe2rgu Mure\u0219', 'M\u0103n\u0103stirea din T\xe2rgu Mure\u0219'],
    ['french_c_cedilla', 'Fran\xe7ais, gar\xe7on, fa\xe7ade', 'Fran\xe7ais, gar\xe7on, fa\xe7ade'],
    ['decomposed_c_cedilla', 'garc\u0327on', 'gar\xe7on'],
    ['whitespace_emoji', 'Bra\u015fov\n\t\U0001f642 ok', 'Bra\u0219ov\n\t\U0001f642 ok'],
    ['mixed_paragraph', 'Ne vedem m\xe2ine \xeen Pia\u0163a Sfatului; \u015ftiu c\u0103 \u015etefan vine \u015fi el.', 'Ne vedem m\xe2ine \xeen Pia\u021ba Sfatului; \u0219tiu c\u0103 \u0218tefan vine \u0219i el.'],
],
}

DATA_SHA256 = "0196ac1b446775af18ba5f7777bf87624363f1369bb399535131c4f112ff1d29"
_blob = json.dumps(DATA, ensure_ascii=False, sort_keys=True).encode("utf-8")
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
HARNESS = '\nimport json, sys, unicodedata\nsrc = sys.stdin.read()\nns = {"__name__": "model_code"}\ntry:\n    exec(compile(src, "<model>", "exec"), ns)\n    f = ns["fix_romanian"]\nexcept BaseException as e:\n    print(json.dumps({"load_error": repr(e)[:300]}))\n    sys.exit(0)\ntests = json.loads(sys.argv[1])\nres = {}\nfor name, inp, exp in tests:\n    try:\n        out = f(inp)\n        res[name] = isinstance(out, str) and unicodedata.normalize("NFC", out) == unicodedata.normalize("NFC", exp)\n    except BaseException:\n        res[name] = False\ntry:\n    p = tests[-1][1]\n    once = f(p)\n    res["idempotent"] = isinstance(once, str) and f(once) == once\nexcept BaseException:\n    res["idempotent"] = False\nprint(json.dumps(res))\n'


@kbench.task(name="Comma Below Code Item", store_task=False)
def code_item(llm, item_id: str, prompt: str) -> dict:
    response = ask(llm, prompt)
    code = extract_python(response)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run([sys.executable, "-c", HARNESS, json.dumps(DATA["tests"])],
                              input=code, capture_output=True, text=True, encoding="utf-8",
                              timeout=30, env=env)
        lines = proc.stdout.strip().splitlines()
        res = json.loads(lines[-1]) if lines else {"load_error": proc.stderr[-300:]}
    except subprocess.TimeoutExpired:
        res = {"load_error": "timeout"}
    names = [t[0] for t in DATA["tests"]] + ["idempotent"]
    passed = [n for n in names if res.get(n) is True]
    score = len(passed) / len(names)
    kbench.assertions.assert_true(score == 1.0, expectation=f"{item_id}: all {len(names)} hidden tests pass")
    return {"item_id": item_id, "score": score, "passed": passed,
            "failed": [n for n in names if n not in passed], "load_error": res.get("load_error"),
            "code": code, "response": response}


@kbench.task(name="Romanian Comma Below 6: Code",
             description="Write fix_romanian(text) to repair cedilla letters; 14 hidden tests incl. uppercase, decomposed forms, French c.")
def romanian_comma_below_6_code(llm) -> float:
    rows, errors = run_items(code_item, llm, pd.DataFrame(DATA["prompts"]))
    save_rows("romanian-comma-below-6-code", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df[["item_id", "score", "failed", "load_error"]].to_string())
    return float(df["score"].mean()) if len(df) else 0.0

# %%
romanian_comma_below_6_code.run(kbench.llm)

# %%
%choose romanian_comma_below_6_code
