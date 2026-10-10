"""Run every generated task locally against fake models, no API calls.

Fake models answer from the gold data and then apply a corruption:
  perfect  - the gold answer
  cedilla  - the gold answer with ș ț replaced by ş ţ (and naive code)
  strip    - the gold answer without any diacritics
  mirror   - copies the input's corruption (cedilla, Cyrillic look-alikes, mojibake) when the
             last prompt has it
  sticky   - like mirror, but remembers a cedilla from any earlier turn of the chat
  normalizer - the gold answer with every cedilla letter turned into the comma letter
               (right for Romanian, wrong for Turkish)
  legacyreader - repairs every wrong form except the old mojibake, which it reads as the cedilla
The expected scores are asserted, so a scoring bug fails loudly.

Usage:  uv run --no-project --with pandas --with-editable ../../_reference/kaggle-benchmarks python src/dry_run.py
"""

from __future__ import annotations

import os
import pathlib
import sys

os.environ["RENDER_SUBRUNS"] = "False"
os.environ.setdefault("KBENCH_UI_MODE", "none")

import kaggle_benchmarks as kbench  # noqa: E402
from kaggle_benchmarks import actors  # noqa: E402
from kaggle_benchmarks.actors.llms import LLMResponse  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
import items as I  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CED = set("şŞţŢ")

GOOD_CODE = '''```python
import unicodedata

def fix_romanian(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return text.translate(str.maketrans({"ş": "ș", "Ş": "Ș", "ţ": "ț", "Ţ": "Ț"}))
```'''
NAIVE_CODE = '''```python
def fix_romanian(text):
    return text.replace("ş", "ș").replace("ţ", "ț")
```'''


def oracle() -> dict[str, str]:
    """Map every prompt text the tasks send to a gold answer."""
    ans = {}
    for i, kind, prompt, req in I.WRITE:
        ans[prompt] = " ".join(req) if req else "Munții sunt albi și liniștiți."
    for i, kind, text in I.ECHO:
        gold = "Vă mulțumim! Vă așteptăm cu drag în Brașov."
        ans[text] = gold
        ans[I.to_cedilla(text)] = gold
        ans[I.ECHO_SUMMARY + text] = gold
        ans[I.ECHO_SUMMARY + I.to_cedilla(text)] = gold
    texts = {i: text for i, _, text in I.ECHO}
    for i, q in I.ECHO_RAG:
        for tx in (texts[i], I.to_cedilla(texts[i])):
            ans[I.ECHO_RAG_PROMPT.format(text=tx, question=q)] = "Șoferii parchează pe strada Mureșenilor."
    for row in build.data_fix():
        ans[I.FIX_LEVELS[row["level"]] + row["text"]] = row["gold"]
    for row in build.data_see():
        ans[row["prompt"]] = row["answer"]
    restore_prompt = ("The following Romanian sentence was typed without diacritics. Rewrite it with the correct "
                      "Romanian diacritics. Change nothing else and reply with the sentence only.\n\n")
    for row in build.data_restore():
        ans[restore_prompt + row["ascii"]] = row["gold"]
    for i, prompt in I.CODE_PROMPTS:
        ans[prompt] = "CODE"
    # Round 2: rows carry their full prompt.
    for row in build.data_echo4():
        ans[row["prompt"]] = GOLD_RO
    for row in build.data_contagion():
        ans[row["prompt"]] = "Șoferii parchează pe strada Mureșenilor."
    for row in build.data_turkish():
        ans[row["prompt"]] = GOLD_TR if row["lang"] == "tr" else GOLD_RO
    for row in build.data_lookalike():
        ans[row["prompt"]] = GOLD_EN
    for row in build.data_wrong_letters():
        ans[row["prompt"]] = GOLD_RO
    return ans


GOLD_RO = "Vă mulțumim! Vă așteptăm cu drag în Brașov."
GOLD_TR = "Teşekkür ederiz, sizi bekliyoruz."
GOLD_EN = "The night train runs between Zürich and München."
TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")
DOT = set("ṣṢṭṬ")
LEGACY = set("ºªþÞ")
ORACLE = oracle()


def corrupt_like(prompt: str, text: str) -> str:
    """Apply to `text` the corruption found in `prompt` (cedilla, dot below, old Romanian mojibake,
    Cyrillic look-alikes, UTF-8 mojibake)."""
    if CED & set(prompt):
        text = I.to_cedilla(text)
    if DOT & set(prompt):
        text = I.to_dot_below(text)
    if LEGACY & set(prompt):
        return I.to_legacy_mojibake(text)
    if any(0x400 <= ord(ch) <= 0x4FF for ch in prompt):
        text = I.to_homoglyph(text)
    if "Ã" in prompt:
        text = I.to_mojibake(text)
    return text


class FakeLLM(actors.LLMChat):
    def __init__(self, policy: str):
        super().__init__(name=f"fake/{policy}")
        self.policy = policy
        self.seen = set()

    def invoke(self, messages, system=None, **kwargs):
        users = [m for m in messages if m.sender.role == "user"]
        prompt = users[-1].content
        # A retry must not resend the question; a second turn is a different question.
        not_duplicated = len(users) == 1 or users[-1].content != users[-2].content
        if self.policy == "picky":
            assert not_duplicated, "fallback duplicated the question"
            if "max_completion_tokens" in kwargs:
                raise TypeError("create() got an unexpected keyword argument 'max_completion_tokens'")
            assert kwargs.get("max_tokens") == 8192, kwargs
        if self.policy == "flaky":
            assert not_duplicated, f"retry duplicated the question: {len(users)} user messages"
            if prompt not in self.seen:
                self.seen.add(prompt)
                raise RuntimeError("Error code: 429 - heavy load")
        gold = ORACLE.get(prompt)
        if gold is None:
            raise KeyError(f"no oracle answer for prompt: {prompt[:80]!r}")
        if gold == "CODE":
            return LLMResponse(content=NAIVE_CODE if self.policy == "cedilla" else GOOD_CODE)
        p = self.policy
        if p == "cedilla":
            out = I.to_cedilla(gold)
        elif p == "mirror":
            out = corrupt_like(prompt, gold)
        elif p == "sticky":
            out = corrupt_like("".join(m.content for m in users if isinstance(m.content, str)), gold)
        elif p == "normalizer":
            out = gold.translate(TO_COMMA)
        elif p == "legacyreader":
            # repairs every wrong form, but reads the old mojibake as the cedilla it encodes
            out = I.to_cedilla(gold) if LEGACY & set(prompt) else gold
        elif p == "strip":
            out = I.strip_diacritics(gold)
        else:
            out = gold
        if p == "thinker":
            out = "<think>Hmm, " + I.to_cedilla("Brașov, ș, ț") + "...</think>\n\n" + out
        return LLMResponse(content=out)


def load_task(slug):
    src = (ROOT / "tasks" / f"{slug}.py").read_text(encoding="ascii")
    body = src.split("\n# %%\nromanian_comma_below_")[0]  # drop the .run() and %choose cells
    ns = {"__name__": f"task_{slug}"}
    exec(compile(body, slug, "exec", dont_inherit=True), ns)
    ns["BACKOFF"] = 0
    return ns


EXPECT = {
    # task: {policy: expected score}
    "romanian-comma-below-1-write": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-2-echo": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-7-echo-with-a-rule": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-3-fix": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-4-see": {"perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-5-restore": {"perfect": 1.0, "cedilla": None, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-6-code": {"perfect": 1.0, "cedilla": None, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    # Round 2
    "romanian-comma-below-8-echo-four-inputs": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-9-contagion": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.2, "sticky": 0.2, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-10-turkish-guests": {"perfect": 1.0, "cedilla": 2 / 3, "strip": 2 / 3, "mirror": 2 / 3, "sticky": 2 / 3, "normalizer": 1 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-11-other-look-alikes": {"perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 0.25, "sticky": 0.25, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-12-turns": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 2 / 3, "sticky": 1 / 3, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
    "romanian-comma-below-13-other-wrong-letters": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "legacyreader": 2 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
}


def main():
    """Usage: dry_run.py [slug fragment ...]  (no argument: every task)."""
    import tempfile
    only = sys.argv[1:]
    os.chdir(tempfile.mkdtemp(prefix="comma-below-dry-"))
    failures = []
    for slug, expect in EXPECT.items():
        if only and not any(f in slug for f in only):
            continue
        ns = load_task(slug)
        func = ns[slug.replace("-", "_")]
        for policy, want in expect.items():
            run = func.run(FakeLLM(policy))
            got = run.result
            status = "ok" if want is None or abs(got - want) < 1e-9 else "FAIL"
            if status == "FAIL":
                failures.append((slug, policy, got, want))
            print(f"{slug:22s} {policy:8s} score={got:.3f} expected={want} {status}")
    assert not failures, failures
    print("dry run passed")


if __name__ == "__main__":
    main()
