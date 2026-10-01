# %% [markdown]
# # Romanian Comma Below 5: Restore
#
# Part of **Comma Below**, a benchmark on one Romanian letter pair: &#x0219; &#x021B; (s and t with a comma below,
# U+0219 and U+021B, the correct Romanian letters) versus &#x015F; &#x0163; (s and t with a cedilla, U+015F and U+0163),
# a legacy encoding error that still fills the Romanian web. They look almost identical and are different
# characters: search, sorting, spell-check and screen readers treat them differently.
#
# **This task:** 30 Romanian sentences typed without diacritics; the model puts them back. Several sentences only differ by context (*peste* over / *pe&#x0219;te* fish, *fata* girl / *fa&#x021B;a* face, *masa* / *mas&#x0103;*).
#
# **Scoring:** a sentence passes when every word matches the gold letter for letter (case and punctuation ignored). Score = share of sentences passed. The results file also records whether the sentence would pass if cedilla letters were accepted, which separates language knowledge from encoding. Every check is done on Unicode code points after NFC normalization. No LLM judge.
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
    {'item_id': 'R01', 'ascii': 'Mananc peste la cina.', 'gold': 'M\u0103n\xe2nc pe\u0219te la cin\u0103.'},
    {'item_id': 'R02', 'ascii': 'Am sarit peste gard.', 'gold': 'Am s\u0103rit peste gard.'},
    {'item_id': 'R03', 'ascii': 'Pestele din lac e proaspat.', 'gold': 'Pe\u0219tele din lac e proasp\u0103t.'},
    {'item_id': 'R04', 'ascii': 'Trecem peste pod si mergem acasa.', 'gold': 'Trecem peste pod \u0219i mergem acas\u0103.'},
    {'item_id': 'R05', 'ascii': 'Fata mea are sapte ani.', 'gold': 'Fata mea are \u0219apte ani.'},
    {'item_id': 'R06', 'ascii': 'Spala-te pe fata inainte de culcare.', 'gold': 'Spal\u0103-te pe fa\u021b\u0103 \xeenainte de culcare.'},
    {'item_id': 'R07', 'ascii': 'In fata casei e un nuc batran.', 'gold': '\xcen fa\u021ba casei e un nuc b\u0103tr\xe2n.'},
    {'item_id': 'R08', 'ascii': 'Fata a venit acasa de la scoala.', 'gold': 'Fata a venit acas\u0103 de la \u0219coal\u0103.'},
    {'item_id': 'R09', 'ascii': 'Am pus masa in bucatarie.', 'gold': 'Am pus masa \xeen buc\u0103t\u0103rie.'},
    {'item_id': 'R10', 'ascii': 'Sunt doua carti pe masa.', 'gold': 'Sunt dou\u0103 c\u0103r\u021bi pe mas\u0103.'},
    {'item_id': 'R11', 'ascii': 'Mama pregateste o masa mare de Craciun.', 'gold': 'Mama preg\u0103te\u0219te o mas\u0103 mare de Cr\u0103ciun.'},
    {'item_id': 'R12', 'ascii': 'Tara noastra are munti frumosi.', 'gold': '\u021aara noastr\u0103 are mun\u021bi frumo\u0219i.'},
    {'item_id': 'R13', 'ascii': 'Muntii Fagaras sunt cei mai inalti din tara.', 'gold': 'Mun\u021bii F\u0103g\u0103ra\u0219 sunt cei mai \xeenal\u021bi din \u021bar\u0103.'},
    {'item_id': 'R14', 'ascii': 'Casa e la sase kilometri de oras.', 'gold': 'Casa e la \u0219ase kilometri de ora\u0219.'},
    {'item_id': 'R15', 'ascii': 'Sa stii ca nu stiu.', 'gold': 'S\u0103 \u0219tii c\u0103 nu \u0219tiu.'},
    {'item_id': 'R16', 'ascii': 'Si el vine, si ea vine.', 'gold': '\u0218i el vine, \u0219i ea vine.'},
    {'item_id': 'R17', 'ascii': 'Scoala incepe luni, pe cincisprezece septembrie.', 'gold': '\u0218coala \xeencepe luni, pe cincisprezece septembrie.'},
    {'item_id': 'R18', 'ascii': 'Pe drum spre Brasov am vazut un urs.', 'gold': 'Pe drum spre Bra\u0219ov am v\u0103zut un urs.'},
    {'item_id': 'R19', 'ascii': 'Ma doare gatul de la frig.', 'gold': 'M\u0103 doare g\xe2tul de la frig.'},
    {'item_id': 'R20', 'ascii': 'Cartile sunt pe raft.', 'gold': 'C\u0103r\u021bile sunt pe raft.'},
    {'item_id': 'R21', 'ascii': 'Tatal lui e pescar la Tulcea.', 'gold': 'Tat\u0103l lui e pescar la Tulcea.'},
    {'item_id': 'R22', 'ascii': 'Am cumparat paine si lapte.', 'gold': 'Am cump\u0103rat p\xe2ine \u0219i lapte.'},
    {'item_id': 'R23', 'ascii': 'Sa ne vedem maine la ora sapte in Piata Sfatului.', 'gold': 'S\u0103 ne vedem m\xe2ine la ora \u0219apte \xeen Pia\u021ba Sfatului.'},
    {'item_id': 'R24', 'ascii': 'Nu-mi place sa astept.', 'gold': 'Nu-mi place s\u0103 a\u0219tept.'},
    {'item_id': 'R25', 'ascii': 'Iasi e un oras din Moldova.', 'gold': 'Ia\u0219i e un ora\u0219 din Moldova.'},
    {'item_id': 'R26', 'ascii': 'Suntem in Romania de doua saptamani.', 'gold': 'Suntem \xeen Rom\xe2nia de dou\u0103 s\u0103pt\u0103m\xe2ni.'},
    {'item_id': 'R27', 'ascii': 'Reintoarcerea acasa a fost lunga.', 'gold': 'Re\xeentoarcerea acas\u0103 a fost lung\u0103.'},
    {'item_id': 'R28', 'ascii': 'A ramas un gest neinteles.', 'gold': 'A r\u0103mas un gest ne\xeen\u021beles.'},
    {'item_id': 'R29', 'ascii': 'Sticla e pe jumatate goala.', 'gold': 'Sticla e pe jum\u0103tate goal\u0103.'},
    {'item_id': 'R30', 'ascii': 'Cand ajungi la Timisoara, suna-ma.', 'gold': 'C\xe2nd ajungi la Timi\u0219oara, sun\u0103-m\u0103.'},
]

DATA_SHA256 = "7ef0f827d068da65d6c693c661aabd37c63758cd34c59b184e86f505ceb1b5fa"
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
PROMPT = ("The following Romanian sentence was typed without diacritics. Rewrite it with the correct "
          "Romanian diacritics. Change nothing else and reply with the sentence only.\n\n")


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

# %%
romanian_comma_below_5_restore.run(kbench.llm)

# %%
%choose romanian_comma_below_5_restore
