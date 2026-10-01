# %% [markdown]
# # Romanian Comma Below 7: Echo With a Rule
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** the cedilla inputs of task 2 (Echo) again, with one added sentence in the system prompt: *Use correct Romanian orthography: write &#x0219; and &#x021B; with a comma below, never &#x015F; or &#x0163; with a cedilla, even if the input uses them.* Does the obvious fix work?
#
# **Scoring:** same as Echo: an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate; compare with the cedilla column of task 2. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
    {'item_id': 'E01-cedilla', 'base_id': 'E01', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Bun\u0103 ziua! A\u015f dori s\u0103 rezerv o camer\u0103 dubl\u0103 \xeen Bra\u015fov pentru dou\u0103 nop\u0163i, de vineri p\xe2n\u0103 duminic\u0103. Ave\u0163i parcare \u015fi mic dejun inclus? Mul\u0163umesc!', 'question': ''},
    {'item_id': 'E02-cedilla', 'base_id': 'E02', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Salut, ajungem \xeen Bra\u015fov s\xe2mb\u0103t\u0103 seara, pe la ora nou\u0103. Se poate face check-in \u015fi dup\u0103 ora zece? Suntem patru persoane \u015fi avem un c\xe2ine mic.', 'question': ''},
    {'item_id': 'E03-cedilla', 'base_id': 'E03', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Bun\u0103 seara. Vreau s\u0103 anulez rezervarea de s\u0103pt\u0103m\xe2na viitoare, pentru c\u0103 mi s-a \xeemboln\u0103vit fiica. \xcemi returna\u0163i avansul? Mul\u0163umesc frumos.', 'question': ''},
    {'item_id': 'E04-cedilla', 'base_id': 'E04', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Bun\u0103! C\xe2\u0163i kilometri sunt de la pensiune p\xe2n\u0103 la Cetatea R\xe2\u015fnov \u015fi la Castelul Bran? Exist\u0103 autobuz sau e mai bine cu ma\u015fina?', 'question': ''},
    {'item_id': 'E05-cedilla', 'base_id': 'E05', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Bun\u0103 ziua, am stat la dumneavoastr\u0103 weekendul trecut \u015fi cred c\u0103 mi-am uitat \xeenc\u0103rc\u0103torul de telefon \xeen camer\u0103. Pute\u0163i verifica, v\u0103 rog?', 'question': ''},
    {'item_id': 'E06-cedilla', 'base_id': 'E06', 'kind': 'reply', 'variant': 'cedilla', 'text': 'Salutare! Organiz\u0103m o \xeent\xe2lnire de familie de treizeci de persoane \xeen octombrie. Ave\u0163i o sal\u0103 \u015fi un meniu cu m\xe2ncare tradi\u0163ional\u0103?', 'question': ''},
    {'item_id': 'E07-cedilla', 'base_id': 'E07', 'kind': 'summary', 'variant': 'cedilla', 'text': 'Prim\u0103ria Bra\u015fov anun\u0163\u0103 c\u0103 Pia\u0163a Sfatului va fi \xeenchis\u0103 traficului auto \xeen weekend, \xeentre orele opt \u015fi dou\u0103zeci, din cauza t\xe2rgului de toamn\u0103. \u015eoferii sunt ruga\u0163i s\u0103 foloseasc\u0103 parc\u0103rile de pe strada Mure\u015fenilor \u015fi de l\xe2ng\u0103 Gara Bra\u015fov.', 'question': ''},
    {'item_id': 'E08-cedilla', 'base_id': 'E08', 'kind': 'summary', 'variant': 'cedilla', 'text': 'Drumul Transf\u0103g\u0103r\u0103\u015fan se \xeenchide \xeen fiecare an la sf\xe2r\u015fitul lunii octombrie, iar redeschiderea are loc, de obicei, la \xeenceputul lui iulie. Autorit\u0103\u0163ile recomand\u0103 turi\u015ftilor s\u0103 verifice starea drumului \xeenainte de plecare, deoarece ninsorile pot ap\u0103rea \u015fi \xeen septembrie.', 'question': ''},
    {'item_id': 'E09-cedilla', 'base_id': 'E09', 'kind': 'summary', 'variant': 'cedilla', 'text': '\u015ecolile din jude\u0163ul Timi\u015f \xee\u015fi vor \xeencepe cursurile cu o s\u0103pt\u0103m\xe2n\u0103 mai t\xe2rziu, dup\u0103 ce mai multe cl\u0103diri au necesitat lucr\u0103ri de repara\u0163ii. P\u0103rin\u0163ii vor fi anun\u0163a\u0163i prin mesaj de fiecare unitate de \xeenv\u0103\u0163\u0103m\xe2nt.', 'question': ''},
    {'item_id': 'E10-cedilla', 'base_id': 'E10', 'kind': 'summary', 'variant': 'cedilla', 'text': 'Festivalul de muzic\u0103 de la Sighi\u015foara a adunat peste cincisprezece mii de spectatori \xeen trei zile. Organizatorii spun c\u0103 biletele pentru edi\u0163ia de anul viitor se vor pune \xeen v\xe2nzare \xeen decembrie, cu reducere pentru studen\u0163i.', 'question': ''},
    {'item_id': 'E11-cedilla', 'base_id': 'E11', 'kind': 'summary', 'variant': 'cedilla', 'text': 'Trenul de noapte dintre Bucure\u015fti \u015fi Ia\u015fi va circula din nou \xeencep\xe2nd cu luna viitoare, dup\u0103 o pauz\u0103 de doi ani. C\u0103l\u0103toria va dura aproximativ \u015fapte ore, iar vagoanele de dormit au fost modernizate.', 'question': ''},
    {'item_id': 'E12-cedilla', 'base_id': 'E12', 'kind': 'summary', 'variant': 'cedilla', 'text': 'Ursul v\u0103zut \xeen cartierul R\u0103c\u0103d\u0103u din Bra\u015fov a fost relocat de jandarmi \xeen cursul nop\u0163ii. Locuitorii sunt sf\u0103tui\u0163i s\u0103 nu lase resturi de m\xe2ncare l\xe2ng\u0103 blocuri \u015fi s\u0103 anun\u0163e prin 112 orice apari\u0163ie a animalelor s\u0103lbatice.', 'question': ''},
    {'item_id': 'Q01-E07-cedilla', 'base_id': 'Q01', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Prim\u0103ria Bra\u015fov anun\u0163\u0103 c\u0103 Pia\u0163a Sfatului va fi \xeenchis\u0103 traficului auto \xeen weekend, \xeentre orele opt \u015fi dou\u0103zeci, din cauza t\xe2rgului de toamn\u0103. \u015eoferii sunt ruga\u0163i s\u0103 foloseasc\u0103 parc\u0103rile de pe strada Mure\u015fenilor \u015fi de l\xe2ng\u0103 Gara Bra\u015fov.', 'question': 'Where are drivers asked to park during the weekend?'},
    {'item_id': 'Q02-E08-cedilla', 'base_id': 'Q02', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Drumul Transf\u0103g\u0103r\u0103\u015fan se \xeenchide \xeen fiecare an la sf\xe2r\u015fitul lunii octombrie, iar redeschiderea are loc, de obicei, la \xeenceputul lui iulie. Autorit\u0103\u0163ile recomand\u0103 turi\u015ftilor s\u0103 verifice starea drumului \xeenainte de plecare, deoarece ninsorile pot ap\u0103rea \u015fi \xeen septembrie.', 'question': 'When does the road usually close, and when does it reopen?'},
    {'item_id': 'Q03-E10-cedilla', 'base_id': 'Q03', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Festivalul de muzic\u0103 de la Sighi\u015foara a adunat peste cincisprezece mii de spectatori \xeen trei zile. Organizatorii spun c\u0103 biletele pentru edi\u0163ia de anul viitor se vor pune \xeen v\xe2nzare \xeen decembrie, cu reducere pentru studen\u0163i.', 'question': "Where did the festival take place, and when do next year's tickets go on sale?"},
    {'item_id': 'Q04-E11-cedilla', 'base_id': 'Q04', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Trenul de noapte dintre Bucure\u015fti \u015fi Ia\u015fi va circula din nou \xeencep\xe2nd cu luna viitoare, dup\u0103 o pauz\u0103 de doi ani. C\u0103l\u0103toria va dura aproximativ \u015fapte ore, iar vagoanele de dormit au fost modernizate.', 'question': 'Between which two cities does the night train run, and how long is the journey?'},
    {'item_id': 'Q05-E07-cedilla', 'base_id': 'Q05', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Prim\u0103ria Bra\u015fov anun\u0163\u0103 c\u0103 Pia\u0163a Sfatului va fi \xeenchis\u0103 traficului auto \xeen weekend, \xeentre orele opt \u015fi dou\u0103zeci, din cauza t\xe2rgului de toamn\u0103. \u015eoferii sunt ruga\u0163i s\u0103 foloseasc\u0103 parc\u0103rile de pe strada Mure\u015fenilor \u015fi de l\xe2ng\u0103 Gara Bra\u015fov.', 'question': 'Which square will be closed to cars, and why?'},
    {'item_id': 'Q06-E08-cedilla', 'base_id': 'Q06', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Drumul Transf\u0103g\u0103r\u0103\u015fan se \xeenchide \xeen fiecare an la sf\xe2r\u015fitul lunii octombrie, iar redeschiderea are loc, de obicei, la \xeenceputul lui iulie. Autorit\u0103\u0163ile recomand\u0103 turi\u015ftilor s\u0103 verifice starea drumului \xeenainte de plecare, deoarece ninsorile pot ap\u0103rea \u015fi \xeen septembrie.', 'question': 'What do the authorities recommend to tourists?'},
    {'item_id': 'Q07-E09-cedilla', 'base_id': 'Q07', 'kind': 'rag', 'variant': 'cedilla', 'text': '\u015ecolile din jude\u0163ul Timi\u015f \xee\u015fi vor \xeencepe cursurile cu o s\u0103pt\u0103m\xe2n\u0103 mai t\xe2rziu, dup\u0103 ce mai multe cl\u0103diri au necesitat lucr\u0103ri de repara\u0163ii. P\u0103rin\u0163ii vor fi anun\u0163a\u0163i prin mesaj de fiecare unitate de \xeenv\u0103\u0163\u0103m\xe2nt.', 'question': "Which county's schools will start later, and why?"},
    {'item_id': 'Q08-E12-cedilla', 'base_id': 'Q08', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Ursul v\u0103zut \xeen cartierul R\u0103c\u0103d\u0103u din Bra\u015fov a fost relocat de jandarmi \xeen cursul nop\u0163ii. Locuitorii sunt sf\u0103tui\u0163i s\u0103 nu lase resturi de m\xe2ncare l\xe2ng\u0103 blocuri \u015fi s\u0103 anun\u0163e prin 112 orice apari\u0163ie a animalelor s\u0103lbatice.', 'question': 'Where was the bear seen, and what should residents do?'},
    {'item_id': 'Q09-E01-cedilla', 'base_id': 'Q09', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Bun\u0103 ziua! A\u015f dori s\u0103 rezerv o camer\u0103 dubl\u0103 \xeen Bra\u015fov pentru dou\u0103 nop\u0163i, de vineri p\xe2n\u0103 duminic\u0103. Ave\u0163i parcare \u015fi mic dejun inclus? Mul\u0163umesc!', 'question': 'What does the guest want to book, and what do they ask about?'},
    {'item_id': 'Q10-E04-cedilla', 'base_id': 'Q10', 'kind': 'rag', 'variant': 'cedilla', 'text': 'Bun\u0103! C\xe2\u0163i kilometri sunt de la pensiune p\xe2n\u0103 la Cetatea R\xe2\u015fnov \u015fi la Castelul Bran? Exist\u0103 autobuz sau e mai bine cu ma\u015fina?', 'question': 'Which two places does the guest ask about?'},
]

DATA_SHA256 = "e78d8a46c06e31cdebf3584be41ffd19e05071eea4721398ed73b6df46a6bd42"
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
SYSTEM = 'You are the booking assistant of a small guesthouse in Brasov, Romania. Reply to the guest in Romanian, in 2 to 4 sentences.'
SUMMARY = 'Summarize the following Romanian news paragraph in Romanian, in at most two sentences.\n\n'
RAG = 'Answer the question using only the text below. Answer in Romanian, in one sentence.\n\nText:\n{text}\n\nQuestion: {question}'
RULE = 'Use correct Romanian orthography: write \u0219 and \u021b with a comma below, never \u015f or \u0163 with a cedilla, even if the input uses them.'


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

# %%
romanian_comma_below_7_echo_with_a_rule.run(kbench.llm)

# %%
%choose romanian_comma_below_7_echo_with_a_rule
