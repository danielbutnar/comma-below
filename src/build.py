"""Generate the six Kaggle task files in tasks/ from src/items.py.

Every generated file is pure ASCII: Romanian letters are written as \\u
escapes, because the Kaggle CLI reads task files with the locale encoding
(cp1250 on the author's laptop) and would otherwise push "BraČ™ov"
instead of "Brașov". Each file also checks a SHA-256 of its decoded data
before running, so any corruption on the way stops the run.

Usage:  uv run --no-project python src/build.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import textwrap

import items as I

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCORING = (ROOT / "src" / "scoring.py").read_text(encoding="utf-8")


def canon_sha(data) -> str:
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def rows_literal(rows: list[dict]) -> str:
    return "[\n" + "".join(f"    {ascii(r)},\n" for r in rows) + "]"


# ---------------------------------------------------------------------------
# Data per task
# ---------------------------------------------------------------------------

def data_write():
    return [
        {"item_id": i, "kind": k, "prompt": p, "required": req}
        for i, k, p, req in I.WRITE
    ]


def data_echo():
    rows = []
    texts = {i: text for i, _, text in I.ECHO}
    for i, kind, text in I.ECHO:
        for variant, t in (("clean", text), ("cedilla", I.to_cedilla(text))):
            rows.append({"item_id": f"{i}-{variant}", "base_id": i, "kind": kind,
                         "variant": variant, "text": t, "question": ""})
    for n, (i, question) in enumerate(I.ECHO_RAG, 1):
        for variant, t in (("clean", texts[i]), ("cedilla", I.to_cedilla(texts[i]))):
            rows.append({"item_id": f"Q{n:02d}-{i}-{variant}", "base_id": f"Q{n:02d}", "kind": "rag",
                         "variant": variant, "text": t, "question": question})
    return rows


def data_fix():
    rows = []
    for i, gold, correct, typo in I.FIX:
        broken = I.to_cedilla(gold.replace(correct, typo, 1))
        for level in I.FIX_LEVELS:
            rows.append({"item_id": f"{i}-{level}", "base_id": i, "level": level,
                         "text": broken, "gold": gold,
                         "correct_word": correct, "typo_word": typo})
    return rows


def data_see():
    q_same = ('Are the two strings below made of exactly the same sequence of Unicode characters?\n\n'
              'A: "{a}"\nB: "{b}"\n\nAnswer with true or false only.')
    q_detect = ('Does the following Romanian sentence contain any cedilla letters (ş, Ş, ţ, Ţ) '
                'instead of the correct comma-below letters (ș, Ș, ț, Ț)?\n\n"{s}"\n\n'
                'Answer with true or false only.')
    q_cp = ('What is the Unicode code point of letter number {pos} in the word "{w}" (counting from 1)? '
            'Answer in the form U+XXXX only.')
    W = I.SEE_WORDS
    ced = I.to_cedilla
    rows = []

    def add(kind, prompt, answer, note):
        rows.append({"item_id": f"S{len(rows) + 1:02d}", "kind": kind, "prompt": prompt,
                     "answer": answer, "note": note})

    # same/different: 8 different, 8 same
    for n, w in enumerate(W[:6]):
        a, b = (w, ced(w)) if n % 2 == 0 else (ced(w), w)
        add("same", q_same.format(a=a, b=b), "false", "comma vs cedilla")
    for w in W[5:8]:
        add("same", q_same.format(a=w, b=w), "true", "both comma")
    for w in (W[1], W[3], W[4]):
        add("same", q_same.format(a=ced(w), b=ced(w)), "true", "both cedilla")
    add("same", q_same.format(a="Brasov", b="Brașov"), "false", "control: visible difference")
    add("same", q_same.format(a="Iași", b="Iasi"), "false", "control: visible difference")
    add("same", q_same.format(a="Sibiu", b="Sibiu"), "true", "control: ascii identical")
    add("same", q_same.format(a="Cluj", b="Cluj"), "true", "control: ascii identical")

    # detection: 3 fully cedilla, 3 with one cedilla word, 6 clean
    S = I.SEE_SENTENCES
    for s in S[0:3]:
        add("detect", q_detect.format(s=ced(s)), "true", "all cedilla")
    for s in S[3:6]:
        words = s.split(" ")
        k = next(j for j, w in enumerate(words) if any(c in w for c in "șȘțȚ"))
        words[k] = ced(words[k])
        add("detect", q_detect.format(s=" ".join(words)), "true", "one cedilla word")
    for s in S[6:12]:
        add("detect", q_detect.format(s=s), "false", "clean")

    # code point: 4 comma, 4 cedilla
    for w, pos in I.SEE_CODEPOINT:
        for form in (w, ced(w)):
            add("codepoint", q_cp.format(pos=pos, w=form), f"U+{ord(form[pos - 1]):04X}",
                "comma" if form == w else "cedilla")
    return rows


def data_restore():
    return [{"item_id": i, "ascii": I.strip_diacritics(g), "gold": g} for i, g in I.RESTORE]


def data_code():
    return {
        "prompts": [{"item_id": i, "prompt": p} for i, p in I.CODE_PROMPTS],
        "tests": [list(t) for t in I.CODE_TESTS],
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

MARKDOWN = """# {title}

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** {what}

**Scoring:** {how} Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.
"""

HEADER = '''# %%
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
{scoring}
# %%
# ---- data ----
{data_name} = {data_literal}

DATA_SHA256 = "{sha}"
_blob = json.dumps({data_name}, ensure_ascii=False, sort_keys=True).encode("utf-8")
assert hashlib.sha256(_blob).hexdigest() == DATA_SHA256, "task data was altered or re-encoded"
print("data ok:", DATA_SHA256[:12])


def save_rows(task_slug, llm, rows, errors):
    """Write every item's response and metrics next to the run file."""
    name = str(getattr(llm, "name", "model")).replace("/", "_").replace("@", "_")
    path = f"{{task_slug}}__{{name}}.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(dumps(r) + "\\n")
        for e in errors:
            fh.write(dumps({{"error": e}}) + "\\n")
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
        cap = {{names[name_idx]: MAX_OUT}} if names[name_idx] else {{}}
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
        {{"item_id": r.params.get("item_id"), "message": (r.error_message or "")[-1500:]}}
        for r in runs.errored_runs
    ]
    if errors:
        print(len(errors), "items errored; last error:", errors[-1]["message"][-600:])
    return rows, errors
'''

FOOTER = '''
# %%
{func}.run(kbench.llm)

# %%
%choose {func}
'''


TASKS = {}


def task(slug, title, what, how, data_name, data, body, func):
    TASKS[slug] = dict(title=title, what=what, how=how, data_name=data_name, data=data, body=body, func=func)


task(
    "romanian-comma-below-1-write", "Romanian Comma Below 1: Write",
    "English prompts ask for Romanian text (translations with ASCII place names, single words, "
    "capitals, JSON, JavaScript, HTML, longer copy). Does the model write the correct letters?",
    "an item passes when the answer has zero cedilla or look-alike letters and every required word "
    "(for example *Timișoara*) appears code-point exact (case-insensitive); items without "
    "required words must contain at least one comma-below letter. Score = share of items passed.",
    "ITEMS", data_write(),
    '''
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
''',
    "romanian_comma_below_1_write",
)

task(
    "romanian-comma-below-2-echo", "Romanian Comma Below 2: Echo",
    "the same Romanian guest messages and news paragraphs arrive twice: once typed correctly and once "
    "typed with cedilla letters. The model replies to the guest, summarizes the paragraph, or answers a "
    "question from it (retrieval style), always in Romanian. Does it copy the user's wrong letters?",
    "a reply passes when it has zero cedilla or look-alike letters and at least one comma-below letter. "
    "Score = pass rate on the **cedilla** inputs; the clean inputs are the control (saved in the results file).",
    "ITEMS", data_echo(),
    '''
SYSTEM = %r
SUMMARY = %r
RAG = %r


@kbench.task(name="Comma Below Echo Item", store_task=False)
def echo_item(llm, item_id: str, base_id: str, kind: str, variant: str, text: str, question: str) -> dict:
    if kind == "reply":
        kbench.system.send(SYSTEM)
        response = ask(llm, text)
    elif kind == "rag":
        response = ask(llm, RAG.format(text=text, question=question))
    else:
        response = ask(llm, SUMMARY + text)
    c = census(response)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and c["comma"] > 0
    # Where do cedilla letters in the answer come from? Words reused from the input vs new words.
    input_words = {w.casefold() for w in words(text)}
    ced_words = [w for w in words(unescape(response)) if any(ch in w for ch in CEDILLA_LETTERS)]
    copied = [w for w in ced_words if w.casefold() in input_words]
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: reply uses comma-below letters only")
    return {"item_id": item_id, "base_id": base_id, "kind": kind, "variant": variant,
            "pass": ok, "cedilla_words": ced_words, "cedilla_words_copied": copied,
            "response": response, **c}


@kbench.task(name="Romanian Comma Below 2: Echo",
             description="Given Romanian input typed with cedilla letters, does the reply copy them? Paired with a clean control.")
def romanian_comma_below_2_echo(llm) -> float:
    rows, errors = run_items(echo_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-2-echo", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("variant")[["pass", "comma", "cedilla"]].mean().to_string())
    ced = df[df["variant"] == "cedilla"]
    return float(ced["pass"].mean()) if len(ced) else 0.0
''' % (I.ECHO_SYSTEM, I.ECHO_SUMMARY, I.ECHO_RAG_PROMPT),
    "romanian_comma_below_2_echo",
)

task(
    "romanian-comma-below-3-fix", "Romanian Comma Below 3: Fix",
    "six Romanian texts typed with cedilla letters, each with one ordinary typo, and three instructions: "
    "a plain *proofread*, *correct the spelling and the diacritics*, and an explicit description of the "
    "cedilla problem. Does the model repair the letters, and does it need to be told?",
    "the rewritten text (the paragraph closest to the answer key; a changelog after it is ignored) passes "
    "when it has zero cedilla or look-alike letters and contains every gold word that has a comma-below "
    "letter. The typo fix is recorded separately. Score = share of answers passed.",
    "ITEMS", data_fix(),
    '''
LEVELS = %r


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
''' % (I.FIX_LEVELS,),
    "romanian_comma_below_3_fix",
)

task(
    "romanian-comma-below-4-see", "Romanian Comma Below 4: See",
    "can the model perceive the difference? Three probes: are two strings identical (8 differ only by "
    "comma vs cedilla or visibly, 8 are identical), does a sentence contain cedilla letters (6 yes, 6 no), "
    "and which code point sits at a given position (4 comma, 4 cedilla).",
    "exact answer match (true/false, or U+XXXX). Score = accuracy over all 36 items; "
    "a coin flip scores about 0.5 on the first two probes.",
    "ITEMS", data_see(),
    '''
@kbench.task(name="Comma Below See Item", store_task=False)
def see_item(llm, item_id: str, kind: str, prompt: str, answer: str, note: str) -> dict:
    response = ask(llm, prompt)
    if kind == "codepoint":
        got = parse_codepoint(response)
        ok = got == answer
    else:
        b = parse_bool(response)
        got = None if b is None else ("true" if b else "false")
        ok = got == answer
    kbench.assertions.assert_true(ok, expectation=f"{item_id} ({note}): expected {answer}")
    return {"item_id": item_id, "kind": kind, "note": note, "answer": answer, "got": got,
            "pass": ok, "response": response}


@kbench.task(name="Romanian Comma Below 4: See",
             description="Can the model tell s/t with a comma below from s/t with a cedilla? Same/different, detection, code point.")
def romanian_comma_below_4_see(llm) -> float:
    rows, errors = run_items(see_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-4-see", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby(["kind", "note"])["pass"].mean().to_string())
    return float(df["pass"].mean()) if len(df) else 0.0
''',
    "romanian_comma_below_4_see",
)

task(
    "romanian-comma-below-5-restore", "Romanian Comma Below 5: Restore",
    "30 Romanian sentences typed without diacritics; the model puts them back. Several sentences only "
    "differ by context (*peste* over / *pește* fish, *fata* girl / *fața* face, *masa* / *masă*).",
    "a sentence passes when every word matches the gold letter for letter (case and punctuation "
    "ignored). Score = share of sentences passed. The results file also records whether the sentence "
    "would pass if cedilla letters were accepted, which separates language knowledge from encoding.",
    "ITEMS", data_restore(),
    '''
PROMPT = ("The following Romanian sentence was typed without diacritics. Rewrite it with the correct "
          "Romanian diacritics. Change nothing else and reply with the sentence only.\\n\\n")


@kbench.task(name="Comma Below Restore Item", store_task=False)
def restore_item(llm, item_id: str, ascii: str, gold: str) -> dict:
    response = ask(llm, PROMPT + ascii)
    exact, acc = restore_score(response, gold)
    fixed = nfc(response).translate(str.maketrans(CEDILLA_LETTERS, COMMA_LETTERS))
    exact_if_cedilla_ok, _ = restore_score(fixed, gold)
    c = census(response)
    kbench.assertions.assert_true(exact, expectation=f"{item_id}: {gold}")
    return {"item_id": item_id, "pass": exact, "word_accuracy": acc,
            "pass_if_cedilla_ok": exact_if_cedilla_ok, "response": response, **c}


@kbench.task(name="Romanian Comma Below 5: Restore",
             description="Restore Romanian diacritics where context decides (peste/peste, fata/fata). Letter-exact, no judge.")
def romanian_comma_below_5_restore(llm) -> float:
    rows, errors = run_items(restore_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-5-restore", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df[["item_id", "pass", "pass_if_cedilla_ok", "word_accuracy", "cedilla"]].to_string())
    return float(df["pass"].mean()) if len(df) else 0.0
''',
    "romanian_comma_below_5_restore",
)

HARNESS = r'''
import json, sys, unicodedata
src = sys.stdin.read()
ns = {"__name__": "model_code"}
try:
    exec(compile(src, "<model>", "exec"), ns)
    f = ns["fix_romanian"]
except BaseException as e:
    print(json.dumps({"load_error": repr(e)[:300]}))
    sys.exit(0)
tests = json.loads(sys.argv[1])
res = {}
for name, inp, exp in tests:
    try:
        out = f(inp)
        res[name] = isinstance(out, str) and unicodedata.normalize("NFC", out) == unicodedata.normalize("NFC", exp)
    except BaseException:
        res[name] = False
try:
    p = tests[-1][1]
    once = f(p)
    res["idempotent"] = isinstance(once, str) and f(once) == once
except BaseException:
    res["idempotent"] = False
print(json.dumps(res))
'''

task(
    "romanian-comma-below-6-code", "Romanian Comma Below 6: Code",
    "the model writes `fix_romanian(text)`, a Python function that repairs cedilla letters. Two prompt "
    "phrasings (one names every letter, one only gives the goal). Hidden tests cover lowercase and "
    "uppercase, decomposed forms (s + U+0327), text that is already correct, French ç that must "
    "not change, whitespace and emoji, and idempotence.",
    "share of the 14 hidden tests passed, averaged over the two prompts. The code runs in a subprocess "
    "with a 30 s timeout.",
    "DATA", data_code(),
    '''
HARNESS = %r


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
''' % (HARNESS,),
    "romanian_comma_below_6_code",
)


ECHO_RULE = ("Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ "
             "with a cedilla, even if the input uses them.")

task(
    "romanian-comma-below-7-echo-with-a-rule", "Romanian Comma Below 7: Echo With a Rule",
    "the cedilla inputs of task 2 (Echo) again, with one added sentence in the system prompt: "
    "*" + ECHO_RULE + "* Does the obvious fix work?",
    "same as Echo: an answer passes when it has zero cedilla or look-alike letters and at least one "
    "comma-below letter. Score = pass rate; compare with the cedilla column of task 2.",
    "ITEMS", [r for r in data_echo() if r["variant"] == "cedilla"],
    '''
SYSTEM = %r
SUMMARY = %r
RAG = %r
RULE = %r


@kbench.task(name="Comma Below Echo Rule Item", store_task=False)
def echo_rule_item(llm, item_id: str, base_id: str, kind: str, variant: str, text: str, question: str) -> dict:
    if kind == "reply":
        kbench.system.send(SYSTEM + " " + RULE)
        response = ask(llm, text)
    else:
        kbench.system.send(RULE)
        response = ask(llm, RAG.format(text=text, question=question) if kind == "rag" else SUMMARY + text)
    c = census(response)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and c["comma"] > 0
    input_words = {w.casefold() for w in words(text)}
    ced_words = [w for w in words(unescape(response)) if any(ch in w for ch in CEDILLA_LETTERS)]
    copied = [w for w in ced_words if w.casefold() in input_words]
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: reply uses comma-below letters only")
    return {"item_id": item_id, "base_id": base_id, "kind": kind, "variant": "cedilla+rule",
            "pass": ok, "cedilla_words": ced_words, "cedilla_words_copied": copied,
            "response": response, **c}


@kbench.task(name="Romanian Comma Below 7: Echo With a Rule",
             description="Echo's cedilla inputs with one system-prompt sentence asking for comma-below letters. Does it fix the copying?")
def romanian_comma_below_7_echo_with_a_rule(llm) -> float:
    rows, errors = run_items(echo_rule_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-7-echo-with-a-rule", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("kind")[["pass", "comma", "cedilla"]].mean().to_string())
    return float(df["pass"].mean())
''' % (I.ECHO_SYSTEM, I.ECHO_SUMMARY, I.ECHO_RAG_PROMPT, ECHO_RULE),
    "romanian_comma_below_7_echo_with_a_rule",
)


def render(slug: str) -> str:
    t = TASKS[slug]
    data = t["data"]
    literal = rows_literal(data) if isinstance(data, list) else (
        "{\n" + "".join(f"    {ascii(k)}: {rows_literal(v) if isinstance(v, list) else ascii(v)},\n"
                        for k, v in data.items()) + "}"
    )
    # Markdown cell: non-ASCII letters become HTML entities, which notebooks render.
    md = MARKDOWN.format(title=t["title"], what=t["what"], how=t["how"])
    md = "".join(c if ord(c) < 128 else f"&#x{ord(c):04X};" for c in md)
    md_cell = "# %% [markdown]\n" + "".join(("# " + line).rstrip() + "\n" for line in md.strip().splitlines())
    code = HEADER.format(
        scoring=SCORING.strip() + "\n",
        data_name=t["data_name"], data_literal=literal, sha=canon_sha(data),
    )
    code += "\n# %%" + t["body"] + FOOTER.format(func=t["func"])
    # Code cells: non-ASCII characters only occur inside ordinary (non-raw) string
    # literals and comments, where a backslash escape keeps the same value.
    code = code.encode("ascii", "backslashreplace").decode("ascii")
    return md_cell + "\n" + code


def main():
    out = ROOT / "tasks"
    out.mkdir(exist_ok=True)
    for slug in TASKS:
        src = render(slug)
        assert src.isascii(), slug
        compile(src.replace("\n%choose", "\n# %choose"), slug, "exec")
        (out / f"{slug}.py").write_text(src, encoding="ascii", newline="\n")
        n = len(TASKS[slug]["data"]) if isinstance(TASKS[slug]["data"], list) else len(TASKS[slug]["data"]["prompts"])
        print(f"{slug}: {n} items, {len(src.encode())} bytes")


if __name__ == "__main__":
    I.check_items()
    main()
