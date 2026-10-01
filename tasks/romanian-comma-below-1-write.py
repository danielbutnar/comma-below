# %% [markdown]
# # Romanian Comma Below 1: Write
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** English prompts ask for Romanian text (translations with ASCII place names, single words, capitals, JSON, JavaScript, HTML, longer copy). Does the model write the correct letters?
#
# **Scoring:** an item passes when the answer has zero cedilla or look-alike letters and every required word (for example *Timi&#x0219;oara*) appears code-point exact (case-insensitive); items without required words must contain at least one comma-below letter. Score = share of items passed. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
    {'item_id': 'W01', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThe train from Timisoara to Iasi stops in Brasov for ten minutes.', 'required': ['Timi\u0219oara', 'Ia\u0219i', 'Bra\u0219ov']},
    {'item_id': 'W02', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nWe spent the weekend in Sighisoara and then drove to Targu Mures.', 'required': ['Sighi\u0219oara', 'Mure\u0219']},
    {'item_id': 'W03', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThe Black Church is the best-known building in Brasov.', 'required': ['Bra\u0219ov']},
    {'item_id': 'W04', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nMy grandmother was born in Constanta and later moved to Pitesti.', 'required': ['Constan\u021ba', 'Pite\u0219ti']},
    {'item_id': 'W05', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nStefan cel Mare ruled Moldavia for forty-seven years.', 'required': ['\u0218tefan']},
    {'item_id': 'W06', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThe Transfagarasan road is closed every winter.', 'required': ['Transf\u0103g\u0103r\u0103\u0219an']},
    {'item_id': 'W07', 'kind': 'translate', 'prompt': "Translate into Romanian. Reply with the translation only.\n\nLet's meet in Piata Sfatului at eight o'clock.", 'required': ['Pia\u021ba Sfatului']},
    {'item_id': 'W08', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThe Cismigiu gardens are in the centre of Bucharest.', 'required': ['Ci\u0219migiu', 'Bucure\u0219ti']},
    {'item_id': 'W09', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThe Rasnov fortress is a short drive from Brasov.', 'required': ['R\xe2\u0219nov', 'Bra\u0219ov']},
    {'item_id': 'W10', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nArges county is famous for the Poenari fortress.', 'required': ['Arge\u0219']},
    {'item_id': 'W11', 'kind': 'word', 'prompt': "What is the Romanian word for 'school'? Reply with the word only.", 'required': ['\u0219coal']},
    {'item_id': 'W12', 'kind': 'word', 'prompt': 'Write the Romanian numbers from one to ten in words, separated by commas.', 'required': ['\u0219ase', '\u0219apte']},
    {'item_id': 'W13', 'kind': 'word', 'prompt': 'List the seven days of the week in Romanian, separated by commas.', 'required': ['mar\u021bi']},
    {'item_id': 'W14', 'kind': 'translate', 'prompt': "Translate into Romanian. Reply with the translation only.\n\nI don't know, but I will find out.", 'required': ['\u0219tiu']},
    {'item_id': 'W15', 'kind': 'translate', 'prompt': 'Translate into Romanian. Reply with the translation only.\n\nThank you very much!', 'required': ['mul\u021bum']},
    {'item_id': 'W16', 'kind': 'word', 'prompt': "What is the Romanian word for 'country' (as in 'my country')? Reply with the word only.", 'required': ['\u021bar']},
    {'item_id': 'W17', 'kind': 'caps', 'prompt': "Write the Romanian word for 'school' in capital letters only. Reply with the word only.", 'required': ['\u0218COAL']},
    {'item_id': 'W18', 'kind': 'json', 'prompt': 'Return a JSON object that maps each of these English city names to its correct Romanian spelling: Brasov, Timisoara, Iasi, Constanta, Pitesti. Return only the JSON.', 'required': ['Bra\u0219ov', 'Timi\u0219oara', 'Ia\u0219i', 'Constan\u021ba', 'Pite\u0219ti']},
    {'item_id': 'W19', 'kind': 'code', 'prompt': 'Write a JavaScript constant array named DAYS with the Romanian names of the days of the week, starting with Monday. Reply with the code only.', 'required': ['mar\u021bi']},
    {'item_id': 'W20', 'kind': 'html', 'prompt': 'Write the HTML <title> element for the homepage of a small guesthouse in Brasov. The title must be in Romanian. Reply with the element only.', 'required': ['Bra\u0219ov']},
    {'item_id': 'W21', 'kind': 'long', 'prompt': 'Write a description of Brasov in Romanian for a tourism website, about 120 words.', 'required': ['Bra\u0219ov']},
    {'item_id': 'W22', 'kind': 'long', 'prompt': 'Write a short email in Romanian (about 80 words) confirming a hotel booking in Timisoara for two nights.', 'required': ['Timi\u0219oara']},
    {'item_id': 'W23', 'kind': 'long', 'prompt': 'Explain in Romanian, in about 100 words, how to make sarmale.', 'required': []},
    {'item_id': 'W24', 'kind': 'long', 'prompt': 'Write two sentences in Romanian about the Carpathian mountains in winter.', 'required': []},
]

DATA_SHA256 = "faf142b73a3dea895c1271df451eea3b29517a20f72ca6ab812cf412853b0f99"
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
@kbench.task(name="Comma Below Write Item", store_task=False)
def write_item(llm, item_id: str, kind: str, prompt: str, required: list) -> dict:
    response = ask(llm, prompt)
    c = census(response)
    miss = missing_required(response, required)
    # Would the answer pass if cedilla letters counted as correct? (knowledge vs encoding)
    as_comma = unescape(response).translate(str.maketrans(CEDILLA_LETTERS, COMMA_LETTERS))
    knows = not missing_required(as_comma, required) and (bool(required) or census(as_comma)["comma"] > 0)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and not miss and (bool(required) or c["comma"] > 0)
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: only comma-below letters, required words present {required}")
    return {"item_id": item_id, "kind": kind, "pass": ok, "knows_spelling": knows,
            "missing": miss, "response": response, **c}


@kbench.task(name="Romanian Comma Below 1: Write",
             description="Does the model write Romanian s/t with a comma below, not a cedilla? Code-point exact.")
def romanian_comma_below_1_write(llm) -> float:
    rows, errors = run_items(write_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-1-write", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df[["item_id", "kind", "pass", "knows_spelling", "comma", "cedilla", "missing"]].to_string())
    return float(df["pass"].mean()) if len(df) else 0.0

# %%
romanian_comma_below_1_write.run(kbench.llm)

# %%
%choose romanian_comma_below_1_write
