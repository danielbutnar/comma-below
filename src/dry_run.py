"""Run every generated task locally against fake models, no API calls.

Fake models answer from the gold data and then apply a corruption:
  perfect  - the gold answer
  cedilla  - the gold answer with ș ț replaced by ş ţ (and naive code)
  strip    - the gold answer without any diacritics
  mirror   - copies cedilla only when the prompt contained cedilla letters
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
    return ans


ORACLE = oracle()


class FakeLLM(actors.LLMChat):
    def __init__(self, policy: str):
        super().__init__(name=f"fake/{policy}")
        self.policy = policy
        self.seen = set()

    def invoke(self, messages, system=None, **kwargs):
        users = [m for m in messages if m.sender.role == "user"]
        prompt = users[-1].content
        if self.policy == "picky":
            assert len(users) == 1, "fallback duplicated the question"
            if "max_completion_tokens" in kwargs:
                raise TypeError("create() got an unexpected keyword argument 'max_completion_tokens'")
            assert kwargs.get("max_tokens") == 8192, kwargs
        if self.policy == "flaky":
            assert len(users) == 1, f"retry duplicated the question: {len(users)} user messages"
            if prompt not in self.seen:
                self.seen.add(prompt)
                raise RuntimeError("Error code: 429 - heavy load")
        gold = ORACLE.get(prompt)
        if gold is None:
            raise KeyError(f"no oracle answer for prompt: {prompt[:80]!r}")
        if gold == "CODE":
            return LLMResponse(content=NAIVE_CODE if self.policy == "cedilla" else GOOD_CODE)
        p = self.policy
        if p == "cedilla" or (p == "mirror" and CED & set(prompt)):
            out = I.to_cedilla(gold)
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
}


def main():
    import tempfile
    os.chdir(tempfile.mkdtemp(prefix="comma-below-dry-"))
    failures = []
    for slug, expect in EXPECT.items():
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
