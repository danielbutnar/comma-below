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
