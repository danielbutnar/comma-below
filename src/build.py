"""Generate the Kaggle task files in tasks/ from src/items.py.

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


ECHO_RULE = I.ECHO_RULE

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


# ---------------------------------------------------------------------------
# Round 2: tasks 8-10. Prompts are built here, so the task code only sends them.
# ---------------------------------------------------------------------------

def data_echo4():
    """Task 2's 22 prompts under four inputs: clean, cedilla, ASCII, cedilla + the task 7 rule."""
    rows = []
    texts = {i: text for i, _, text in I.ECHO}
    variants = (("clean", lambda t: t, False), ("cedilla", I.to_cedilla, False),
                ("ascii", I.strip_diacritics, False), ("cedilla+rule", I.to_cedilla, True))

    def system_for(kind, rule):
        if kind == "reply":
            return I.ECHO_SYSTEM + (" " + I.ECHO_RULE if rule else "")
        return I.ECHO_RULE if rule else ""

    for i, kind, text in I.ECHO:
        for variant, f, rule in variants:
            t = f(text)
            prompt = t if kind == "reply" else I.ECHO_SUMMARY + t
            rows.append({"item_id": f"{i}-{variant}", "base_id": i, "kind": kind, "variant": variant,
                         "system": system_for(kind, rule), "prompt": prompt, "text": t, "gold": text})
    for n, (i, question) in enumerate(I.ECHO_RAG, 1):
        for variant, f, rule in variants:
            t = f(texts[i])
            rows.append({"item_id": f"Q{n:02d}-{i}-{variant}", "base_id": f"Q{n:02d}", "kind": "rag",
                         "variant": variant, "system": system_for("rag", rule),
                         "prompt": I.ECHO_RAG_PROMPT.format(text=t, question=question), "text": t,
                         "gold": texts[i]})
    return rows


def data_contagion():
    """Four documents, one question about one of them; 0, 1 or 3 of the others typed with cedilla."""
    texts = {i: text for i, _, text in I.ECHO}
    pool = I.CONTAGION_POOL
    seen = {}
    rows = []
    for n, (target, question) in enumerate(I.CONTAGION):
        k = pool.index(target)
        repeat = seen.get(target, 0)
        seen[target] = repeat + 1
        step = 1 if repeat == 0 else -1  # a repeated target gets the other three neighbours
        others = [pool[(k + step * (j + 1)) % len(pool)] for j in range(3)]
        pos = n % 4
        one = others[n % 3]  # the single cedilla document in condition clean-1
        for cond in I.CONTAGION_CONDITIONS:
            target_variant, k_other = cond.split("-")
            k_other = int(k_other)
            ced_others = set() if k_other == 0 else ({one} if k_other == 1 else set(others))
            order = others[:pos] + [target] + others[pos:]
            docs = []
            for d in order:
                cedilla = (d == target and target_variant == "cedilla") or (d != target and d in ced_others)
                docs.append(I.to_cedilla(texts[d]) if cedilla else texts[d])
            block = "\n\n".join(f"Document {j + 1}:\n{t}" for j, t in enumerate(docs))
            rows.append({"item_id": f"K{n + 1:02d}-{target}-{cond}", "set_id": f"K{n + 1:02d}",
                         "target": target, "cond": cond, "target_variant": target_variant,
                         "k_other": k_other, "target_pos": pos, "order": order, "docs": docs,
                         "prompt": I.CONTAGION_PROMPT.format(docs=block, question=question)})
    return rows


def data_turkish():
    """Turkish guests (ş is correct there) and Romanian guests typed with cedilla, under two rules."""
    rules = {"none": "", "rule": I.ECHO_RULE, "scoped": I.TR_RULE_SCOPED}
    rows = []
    for i, text in I.TURKISH:
        for r in ("none", "rule", "scoped"):
            rows.append({"item_id": f"{i}-{r}", "base_id": i, "lang": "tr", "rule": r,
                         "system": (I.TR_SYSTEM + " " + rules[r]).strip(), "prompt": text})
    for i, kind, text in I.ECHO:
        if kind != "reply":
            continue
        for r in ("rule", "scoped"):
            rows.append({"item_id": f"{i}-ro-{r}", "base_id": i, "lang": "ro", "rule": r,
                         "system": (I.TR_SYSTEM + " " + rules[r]).strip(), "prompt": I.to_cedilla(text)})
    return rows


# Word-level helpers used only by the Round 2 tasks (tasks 1-7 stay byte-identical).
ROUND2_HELPERS = '''
_TO_ASCII = str.maketrans({0x103: "a", 0x102: "A", 0xE2: "a", 0xC2: "A", 0xEE: "i", 0xCE: "I",
                           0x219: "s", 0x218: "S", 0x21B: "t", 0x21A: "T",
                           0x15F: "s", 0x15E: "S", 0x163: "t", 0x162: "T"})
RO_DIACRITICS = "".join(map(chr, (0x103, 0x102, 0xE2, 0xC2, 0xEE, 0xCE))) + COMMA_LETTERS + CEDILLA_LETTERS


def ascii_key(word):
    return nfc(word).translate(_TO_ASCII).casefold()


def st_forms(response, gold):
    """How the answer spells the gold's s/t words: comma (right), cedilla, or no diacritic.

    A word counts when its ASCII form matches a gold word that has a comma-below letter.
    """
    want = {ascii_key(w): w.casefold() for w in words(gold) if any(c in w for c in COMMA_LETTERS)}
    out = {"st_total": 0, "st_comma": 0, "st_cedilla": 0, "st_ascii": 0, "st_other": 0}
    for w in words(unescape(response)):
        key = ascii_key(w)
        if key not in want:
            continue
        out["st_total"] += 1
        if w.casefold() == want[key]:
            out["st_comma"] += 1
        elif any(c in w for c in CEDILLA_LETTERS):
            out["st_cedilla"] += 1
        elif not any(c in w for c in RO_DIACRITICS):
            out["st_ascii"] += 1
        else:
            out["st_other"] += 1
    return out
'''

task(
    "romanian-comma-below-8-echo-four-inputs", "Romanian Comma Below 8: Echo, Four Inputs",
    "task 2's 22 prompts (guest replies, news summaries, retrieval-style answers) under four inputs: "
    "typed correctly, typed with cedilla letters, typed without any diacritics (ASCII), and typed with "
    "cedilla plus task 7's one-sentence rule in the system prompt. Run on every model Kaggle serves, so "
    "model generations and sizes can be compared on identical items. "
    "Pre-registered predictions (written before any run): (1) clean input stays near 100 % for every "
    "model; (2) cedilla input fails far more often than ASCII input, because a missing diacritic looks "
    "broken and a cedilla does not; (3) newer models in a family copy the cedilla at least as often as "
    "older ones; (4) the rule lifts cedilla input to at least 90 % for most models.",
    "an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. "
    "Score = pass rate on the **cedilla** inputs (as in task 2). The results file also records, for every "
    "answer, how each s/t word of the source was spelled (comma, cedilla, or no diacritic).",
    "ITEMS", data_echo4(),
    ROUND2_HELPERS + '''

@kbench.task(name="Comma Below Echo4 Item", store_task=False)
def echo4_item(llm, item_id: str, base_id: str, kind: str, variant: str, system: str, prompt: str,
               text: str, gold: str) -> dict:
    if system:
        kbench.system.send(system)
    response = ask(llm, prompt)
    c = census(response)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and c["comma"] > 0
    input_words = {w.casefold() for w in words(text)}
    ced_words = [w for w in words(unescape(response)) if any(ch in w for ch in CEDILLA_LETTERS)]
    copied = [w for w in ced_words if w.casefold() in input_words]
    st = st_forms(response, gold)
    any_diacritic = any(ch in nfc(unescape(response)) for ch in RO_DIACRITICS)
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: answer uses comma-below letters only")
    return {"item_id": item_id, "base_id": base_id, "kind": kind, "variant": variant, "pass": ok,
            "cedilla_words": ced_words, "cedilla_words_copied": copied, "any_diacritic": any_diacritic,
            "response": response, **c, **st}


@kbench.task(name="Romanian Comma Below 8: Echo, Four Inputs",
             description="Task 2's prompts typed clean, with cedilla, without diacritics, and with cedilla plus a rule. Code-point exact.")
def romanian_comma_below_8_echo_four_inputs(llm) -> float:
    rows, errors = run_items(echo4_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-8-echo-four-inputs", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("variant")[["pass", "comma", "cedilla", "st_total", "st_cedilla", "st_ascii"]].mean().to_string())
    ced = df[df["variant"] == "cedilla"]
    return float(ced["pass"].mean()) if len(ced) else 0.0
''',
    "romanian_comma_below_8_echo_four_inputs",
)

task(
    "romanian-comma-below-9-contagion", "Romanian Comma Below 9: Contagion",
    "four Romanian news paragraphs as documents and one question about one of them, answered in Romanian. "
    "Five conditions per question: everything clean; the target clean and one or all three other "
    "documents typed with cedilla; the target typed with cedilla and the others clean; everything typed "
    "with cedilla. When the target is clean, any cedilla letter in the answer came from somewhere else. "
    "Pre-registered predictions (written before any run): (1) with a clean target, the answer stays "
    "clean for most models even when the other three documents are cedilla, because answers reuse the "
    "target's words; (2) the models that rewrote whole answers in cedilla in task 2 are the ones whose "
    "clean-target answers get infected; (3) a cedilla target is copied less when the other documents "
    "are clean.",
    "an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. "
    "Score = pass rate over all 40 items. Every cedilla word in an answer is traced to the target "
    "document, another document, or neither.",
    "ITEMS", data_contagion(),
    '''

@kbench.task(name="Comma Below Contagion Item", store_task=False)
def contagion_item(llm, item_id: str, set_id: str, target: str, cond: str, target_variant: str,
                   k_other: int, target_pos: int, order: list, docs: list, prompt: str) -> dict:
    response = ask(llm, prompt)
    c = census(response)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and c["comma"] > 0
    target_words = {w.casefold() for w in words(docs[target_pos])}
    other_words = {w.casefold() for j, d in enumerate(docs) if j != target_pos for w in words(d)}
    ced = [w for w in words(unescape(response)) if any(ch in w for ch in CEDILLA_LETTERS)]
    from_target = [w for w in ced if w.casefold() in target_words]
    from_others = [w for w in ced if w.casefold() not in target_words and w.casefold() in other_words]
    novel = [w for w in ced if w.casefold() not in target_words and w.casefold() not in other_words]
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: answer uses comma-below letters only")
    return {"item_id": item_id, "set_id": set_id, "target": target, "cond": cond,
            "target_variant": target_variant, "k_other": k_other, "target_pos": target_pos, "pass": ok,
            "cedilla_words": ced, "from_target": from_target, "from_others": from_others,
            "novel": novel, "response": response, **c}


@kbench.task(name="Romanian Comma Below 9: Contagion",
             description="Four documents, some typed with cedilla; a question about one. Does the cedilla spread to the answer?")
def romanian_comma_below_9_contagion(llm) -> float:
    rows, errors = run_items(contagion_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-9-contagion", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("cond")[["pass", "comma", "cedilla"]].mean().to_string())
    return float(df["pass"].mean())
''',
    "romanian_comma_below_9_contagion",
)

task(
    "romanian-comma-below-10-turkish-guests", "Romanian Comma Below 10: Turkish Guests",
    "the cedilla letter is wrong in Romanian and right in Turkish (*teşekkür*, *şehir*). Eight Turkish "
    "guest messages are answered with no rule, with task 7's rule (*never ş or ţ*), and with a rule scoped "
    "to Romanian; six Romanian messages typed with cedilla are answered under both rules. Does the fix "
    "for Romanian break Turkish? "
    "Pre-registered predictions (written before any run): (1) without a rule, Turkish replies keep ş; "
    "(2) task 7's rule makes some models write Turkish with the Romanian comma letter; (3) the scoped "
    "rule keeps Turkish intact and still fixes Romanian.",
    "a Turkish reply passes when its Turkish words contain the Turkish ş and never the comma-below ș "
    "(Romanian place names such as Brașov are left out of the count: either spelling is defensible "
    "there); a Romanian reply passes when it has zero cedilla or look-alike letters and at least one "
    "comma-below letter. Score = pass rate over all 36 items.",
    "ITEMS", data_turkish(),
    '''
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
''',
    "romanian_comma_below_10_turkish_guests",
)


def data_lookalike():
    """English paragraphs: clean; Cyrillic look-alikes in every word (dense) or only in the accented
    names (sparse), which look right; mojibake in the same names, which looks broken."""
    variants = (("clean", lambda t: t), ("cyrillic-all", I.to_homoglyph), ("cyrillic-names", I.to_homoglyph_names),
                ("mojibake", I.to_mojibake))
    rows = []
    for i, text, question in I.LOOKALIKE:
        for kind in ("summary", "rag"):
            for variant, f in variants:
                t = f(text)
                prompt = I.LOOKALIKE_SUMMARY + t if kind == "summary" else I.LOOKALIKE_RAG.format(text=t, question=question)
                rows.append({"item_id": f"{i}-{kind}-{variant}", "base_id": i, "kind": kind,
                             "variant": variant, "prompt": prompt, "gold": text})
    return rows


def data_turns():
    """Two summaries in one chat; the second is scored."""
    texts = {i: text for i, _, text in I.ECHO}
    rows = []
    for a, b in I.TURN_PAIRS:
        for cond in I.TURN_CONDITIONS:
            first, second = cond.split(">")
            ta = I.to_cedilla(texts[a]) if first == "cedilla" else texts[a]
            tb = I.to_cedilla(texts[b]) if second == "cedilla" else texts[b]
            rows.append({"item_id": f"{a}{b}-{cond}", "pair_id": f"{a}{b}", "cond": cond,
                         "first_prompt": I.ECHO_SUMMARY + ta, "second_prompt": I.ECHO_SUMMARY + tb,
                         "first_text": ta, "second_text": tb})
    return rows


task(
    "romanian-comma-below-11-other-look-alikes", "Romanian Comma Below 11: Other Look-Alikes",
    "the Echo design outside Romanian. Six English news paragraphs with accented names (Zürich, Café "
    "Müller, Málaga) are summarized or used to answer a question, typed four ways: correctly; with "
    "Cyrillic look-alike letters (а с е о р for a c e o p) in every word; with Cyrillic look-alikes only "
    "inside the accented names; and as mojibake in the same names (UTF-8 read as Windows-1252, "
    "*ZÃ¼rich*), which looks broken. "
    "Pre-registered predictions (written before any run): (1) clean input stays near 100 %; (2) Cyrillic "
    "look-alikes are copied into answers far more often than mojibake, because mojibake looks broken and "
    "look-alikes do not; (3) the models that copy the Romanian cedilla most (task 8) also copy the "
    "Cyrillic look-alikes most. "
    "Version 2 note: version 1 had only the dense Cyrillic variant (about a third of all letters "
    "replaced, versus about 2 % for the Romanian cedilla). Its single run (Gemini 3.7 Flash) copied none "
    "of it, so version 2 adds look-alikes confined to the names, the same words mojibake touches. The "
    "predictions are unchanged.",
    "a clean or Cyrillic-input answer passes when it contains no Cyrillic letter; a mojibake-input answer "
    "passes when it contains no mojibake marker (Ã or Â). Score = pass rate over all 48 items.",
    "ITEMS", data_lookalike(),
    '''
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
''',
    "romanian_comma_below_11_other_look_alikes",
)

task(
    "romanian-comma-below-12-turns", "Romanian Comma Below 12: Turns",
    "two news summaries in one chat. The second summary is scored: after a first text typed with cedilla, "
    "is the summary of a clean second text still written with cedilla? After a clean first text, is a "
    "cedilla second text copied less than in task 2? "
    "Pre-registered predictions (written before any run): (1) a cedilla first turn infects some clean "
    "second summaries, mostly for models whose first summary was itself in cedilla; (2) a clean first "
    "turn does not protect a cedilla second text much.",
    "the second summary passes when it has zero cedilla or look-alike letters and at least one "
    "comma-below letter. Score = pass rate of the second summaries over all 18 conversations.",
    "ITEMS", data_turns(),
    '''

@kbench.task(name="Comma Below Turns Item", store_task=False)
def turns_item(llm, item_id: str, pair_id: str, cond: str, first_prompt: str, second_prompt: str,
               first_text: str, second_text: str) -> dict:
    first = ask(llm, first_prompt)
    second = ask(llm, second_prompt)
    c1, c2 = census(first), census(second)
    ok = c2["cedilla"] == 0 and c2["lookalike"] == 0 and c2["comma"] > 0
    second_words = {w.casefold() for w in words(second_text)}
    ced2 = [w for w in words(unescape(second)) if any(ch in w for ch in CEDILLA_LETTERS)]
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: second summary uses comma-below letters only")
    return {"item_id": item_id, "pair_id": pair_id, "cond": cond, "pass": ok,
            "first_cedilla": c1["cedilla"], "first_comma": c1["comma"],
            "second_cedilla": c2["cedilla"], "second_comma": c2["comma"],
            "cedilla_words": ced2, "cedilla_words_copied": [w for w in ced2 if w.casefold() in second_words],
            "first": first, "response": second}


@kbench.task(name="Romanian Comma Below 12: Turns",
             description="Two summaries in one chat: does a cedilla first text infect the second summary?")
def romanian_comma_below_12_turns(llm) -> float:
    rows, errors = run_items(turns_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-12-turns", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    print(df.groupby("cond")[["pass", "first_cedilla", "second_cedilla"]].mean().to_string())
    return float(df["pass"].mean())
''',
    "romanian_comma_below_12_turns",
)


def data_wrong_letters():
    """Task 8's 16 summaries and document questions under five inputs (task 13)."""
    texts = {i: text for i, _, text in I.ECHO}
    variants = (("cedilla", I.to_cedilla, ""), ("dot", I.to_dot_below, ""),
                ("legacy", I.to_legacy_mojibake, ""), ("cedilla+scoped", I.to_cedilla, I.TR_RULE_SCOPED),
                ("cedilla+rule", I.to_cedilla, I.ECHO_RULE))
    rows = []
    for i, kind, text in I.ECHO:
        if kind != "summary":
            continue
        for variant, f, system in variants:
            t = f(text)
            rows.append({"item_id": f"{i}-{variant}", "base_id": i, "kind": kind, "variant": variant,
                         "system": system, "prompt": I.ECHO_SUMMARY + t, "text": t, "gold": text})
    for n, (i, question) in enumerate(I.ECHO_RAG, 1):
        for variant, f, system in variants:
            t = f(texts[i])
            rows.append({"item_id": f"Q{n:02d}-{i}-{variant}", "base_id": f"Q{n:02d}", "kind": "rag",
                         "variant": variant, "system": system,
                         "prompt": I.ECHO_RAG_PROMPT.format(text=t, question=question), "text": t,
                         "gold": texts[i]})
    return rows


task(
    "romanian-comma-below-13-other-wrong-letters", "Romanian Comma Below 13: Other Wrong Letters",
    "task 8's 16 prompts where models reuse the source's words (6 news summaries and 10 questions about a "
    "document, built on 8 source texts), with the source typed five ways: (a) with the cedilla, as in task 8 "
    "(the control); (b) with s and t with a dot below (ṣ ṭ): near-identical to the right letters and real "
    "letters elsewhere (Yoruba, transliteration), but not used in Romanian; (c) as the old mojibake of "
    "Romanian web pages and subtitles (Windows-1250 bytes read as Windows-1252: Brașov becomes Braºov, "
    "țară becomes þarã), which also turns ă into ã; (d) with the cedilla and task 10's scoped rule in the "
    "system prompt; (e) with the cedilla and task 7's full rule, for a same-run comparison with (d). Every "
    "s/t letter of the source's words is scored in the answer as kept in the input's form, comma below "
    "(right), cedilla, or bare; ă is scored apart. "
    "Pre-registered predictions (written before any run; new runs on the same 16 prompts): "
    "(1) Main test: the dot below is kept in a smaller share of s/t letters than the cedilla, on the same "
    "models and prompts (paired difference, 95 % interval below zero). Kept about as often would mean any "
    "letter-like substitute gets copied; kept less often, that the familiar wrong spelling is what gets "
    "kept. (2) The old mojibake is kept less often than the cedilla; kept about as often would mean models "
    "copy whatever the input has. Romanian mojibake looks rare in training text (no tokenizer merges for "
    "it), so here 'seen in Romanian text' and 'the cedilla is special' predict the same result. "
    "(3) Repaired dot-below and mojibake letters become comma-below letters, not the cedilla, in at least "
    "90 % of cases. (4) Both rules give at least 90 % clean answers, and the scoped rule is within 5 points "
    "of the full rule. (5) Replication of task 8: in cedilla answers that keep every cedilla of the input, "
    "at least 80 % of the s/t words the model adds itself (not in the source and not inflections of source "
    "words: no shared start of 5 letters) have the cedilla; in "
    "answers that keep only some, at most 30 %. Answers that comment on the encoding are flagged and "
    "reported with and without; answers with none of the source's s/t words count as no data.",
    "an answer passes when it has no cedilla, dot-below, mojibake (º ª þ Þ) or "
    "look-alike (ã ǎ) letters and at least one comma-below letter. Score = pass rate on the "
    "three wrong-letter inputs without a rule (a, b, c). The results file records, for every answer, "
    "each s/t and ă letter of the source's words as written (slot counts), the word-level forms as in "
    "task 8, the wrong-form words and which of them were copied from the input, and the words with which "
    "an answer comments on the encoding.",
    "ITEMS", data_wrong_letters(),
    '''
DOT_LETTERS = "".join(map(chr, (0x1E62, 0x1E63, 0x1E6C, 0x1E6D)))  # S s T t with a dot below
LEGACY_LETTERS = "".join(map(chr, (0xAA, 0xBA, 0xDE, 0xFE)))  # cedilla S s T t, Windows-1250 read as 1252
WRONG_LETTERS = CEDILLA_LETTERS + DOT_LETTERS + LEGACY_LETTERS
A_BREVE = "".join(map(chr, (0x102, 0x103)))
A_TILDE = "".join(map(chr, (0xC3, 0xE3)))
# An answer that talks about the letters (in English or Romanian) may quote the broken text on purpose.
ENCODING_TALK = re.compile(r"encod|codific|diacritic|mojibake|unicode|utf|1250|1252|[cs]edil|virgul|ortograf|"
                           r"caracter|afi.a|corupt", re.I)
_KEY13 = str.maketrans({0x103: "a", 0x102: "A", 0xE2: "a", 0xC2: "A", 0xEE: "i", 0xCE: "I",
                        0x219: "s", 0x218: "S", 0x21B: "t", 0x21A: "T",
                        0x15F: "s", 0x15E: "S", 0x163: "t", 0x162: "T",
                        0x1E63: "s", 0x1E62: "S", 0x1E6D: "t", 0x1E6C: "T",
                        0xBA: "s", 0xAA: "S", 0xFE: "t", 0xDE: "T", 0xE3: "a", 0xC3: "A"})


def key13(word):
    return nfc(word).translate(_KEY13).casefold()


def st_forms13(response, gold):
    """How the answer spells the source's s/t words: comma, cedilla, dot, legacy mojibake, or none.

    A word counts when its key (every form of s, t and a folded) matches a source word with a
    comma-below letter. The form is judged by the s/t letters only; a and a-tilde are counted apart.
    """
    want = {key13(w) for w in words(gold) if any(c in w for c in COMMA_LETTERS)}
    out = dict.fromkeys(("st_total", "st_comma", "st_cedilla", "st_dot", "st_legacy", "st_ascii"), 0)
    for w in words(unescape(response)):
        if key13(w) not in want:
            continue
        out["st_total"] += 1
        if any(c in w for c in CEDILLA_LETTERS):
            out["st_cedilla"] += 1
        elif any(c in w for c in DOT_LETTERS):
            out["st_dot"] += 1
        elif any(c in w for c in LEGACY_LETTERS):
            out["st_legacy"] += 1
        elif any(c in w for c in COMMA_LETTERS):
            out["st_comma"] += 1
        else:
            out["st_ascii"] += 1
    return out


def slots13(response, gold):
    """Letter by letter: how the answer writes each s/t and each a-breve of the source's words.

    A response word is aligned with the source word that has the same key; forms are 1:1 letter swaps,
    so the two words have the same length and every letter has a slot.
    """
    want = {}
    for w in words(gold):
        if any(c in w for c in COMMA_LETTERS + A_BREVE):
            want.setdefault(key13(w), w)
    out = dict.fromkeys(("sl_st", "sl_st_comma", "sl_st_cedilla", "sl_st_dot", "sl_st_legacy", "sl_st_bare",
                         "sl_st_other", "sl_a", "sl_a_breve", "sl_a_tilde", "sl_a_bare", "sl_a_other"), 0)
    for w in words(unescape(response)):
        g = want.get(key13(w))
        if g is None or len(g) != len(w):
            continue
        for x, y in zip(g, w):
            if x in COMMA_LETTERS:
                out["sl_st"] += 1
                form = ("comma" if y in COMMA_LETTERS else "cedilla" if y in CEDILLA_LETTERS else
                        "dot" if y in DOT_LETTERS else "legacy" if y in LEGACY_LETTERS else
                        "bare" if y in "sStT" else "other")
                out["sl_st_" + form] += 1
            elif x in A_BREVE:
                out["sl_a"] += 1
                form = "breve" if y in A_BREVE else "tilde" if y in A_TILDE else "bare" if y in "aA" else "other"
                out["sl_a_" + form] += 1
    return out


@kbench.task(name="Comma Below Wrong Letters Item", store_task=False)
def wrong_letters_item(llm, item_id: str, base_id: str, kind: str, variant: str, system: str, prompt: str,
                       text: str, gold: str) -> dict:
    if system:
        kbench.system.send(system)
    response = ask(llm, prompt)
    c = census(response)
    t = nfc(unescape(response))
    dot = sum(t.count(ch) for ch in DOT_LETTERS)
    legacy = sum(t.count(ch) for ch in LEGACY_LETTERS)
    ok = c["cedilla"] == 0 and c["lookalike"] == 0 and dot == 0 and legacy == 0 and c["comma"] > 0
    input_words = {w.casefold() for w in words(text)}
    wrong = [w for w in words(unescape(response)) if any(ch in w for ch in WRONG_LETTERS)]
    copied = [w for w in wrong if w.casefold() in input_words]
    st = st_forms13(response, gold)
    sl = slots13(response, gold)
    kbench.assertions.assert_true(ok, expectation=f"{item_id}: answer uses comma-below letters only")
    return {"item_id": item_id, "base_id": base_id, "kind": kind, "variant": variant, "pass": ok,
            "dot": dot, "legacy": legacy, "a_breve": sum(t.count(ch) for ch in A_BREVE),
            "a_tilde": sum(t.count(ch) for ch in A_TILDE), "wrong_words": wrong,
            "wrong_words_copied": copied,
            "encoding_talk": sorted({m.group(0).casefold() for m in ENCODING_TALK.finditer(t)}),
            "response": response, **c, **st, **sl}


@kbench.task(name="Romanian Comma Below 13: Other Wrong Letters",
             description="Task 8's summaries and questions typed with the cedilla, a dot below, or old mojibake. Code-point exact.")
def romanian_comma_below_13_other_wrong_letters(llm) -> float:
    rows, errors = run_items(wrong_letters_item, llm, pd.DataFrame(ITEMS))
    save_rows("romanian-comma-below-13-other-wrong-letters", llm, rows, errors)
    df = pd.DataFrame(rows)
    if df.empty:
        return 0.0
    cols = ["pass", "sl_st", "sl_st_comma", "sl_st_cedilla", "sl_st_dot", "sl_st_legacy", "sl_st_bare",
            "sl_a", "sl_a_breve", "sl_a_tilde"]
    print(df.groupby("variant")[cols].mean().to_string())
    wrong = df[df["variant"].isin(["cedilla", "dot", "legacy"])]
    return float(wrong["pass"].mean()) if len(wrong) else 0.0
''',
    "romanian_comma_below_13_other_wrong_letters",
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
