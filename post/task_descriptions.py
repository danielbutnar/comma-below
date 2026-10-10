"""Write post/kaggle-task-descriptions.md: the text to paste into each Kaggle task's Description field.

The text is the markdown cell at the top of each task notebook (src/build.py), so the two can't drift
apart. Three things are added here and not in the notebooks: the inputs and the pre-registered
predictions are shown as lists (their words are unchanged, which block() asserts), notes written
after the runs are added under their own heading, and every task links the write-up and its code.
tasks/*.py stay as they ran.
Usage:  uv run --no-project python post/task_descriptions.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import build  # noqa: E402

WRITE_UP = "https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a"
REPO = "https://github.com/danielbutnar/comma-below"
HEAD = """# Kaggle task descriptions

Paste one block into each task's Description field on Kaggle:

1. Open the task page (the link under each heading) and edit its Description.
2. Copy the block from "Part of **Comma Below**" down to the "Code:" line and paste it as Markdown.
3. Save, then open the page in a logged-out window to check that it shows.

Each block is the first cell of that task's notebook, generated from src/build.py by
post/task_descriptions.py. The pre-registered predictions are word for word as pushed before the runs;
only the layout differs (they, and task 13's five inputs, are shown as lists). The notes under "Added
after the runs" were written after the runs and are not part of the pushed text.
"""

# The one-line descriptions in the task code (@kbench.task(description=...)) were typed in ASCII, which
# turned the letters under test into typos. They stay as they ran; the notes below give the intended text.
FLATTENED = {"(peste/peste, fata/fata)": "(peste/pește, fata/fața)", "French c.": "French ç."}

# Notes written after the runs, outside the pre-registered text. The numbers come from the stored answers
# in results/raw (see README.md, "Known issues in the pushed tasks").
NOTES = {
    "romanian-comma-below-4-see": [
        "The scorer takes the first true/false or U+XXXX in each answer, so \"exact answer match\" above "
        "means that first match. The prompts ask for the answer alone, and most models give it that way. "
        "DeepSeek-R1 listed every letter's code point before giving the right one, so its six code-point "
        "answers count as wrong here: it shows 83 %, and scored on its final answers it gets 36 of 36. "
        "Gemini 3.5 Flash-Lite shows 83 % and gets 32 of 36 on its final answers. No other model changes.",
    ],
    "romanian-comma-below-6-code": [
        "Items that hit provider errors are left out of a run's score, and a run with no completed item "
        "scores 0: gpt-oss-120b's latest run shows 0 because both prompts hit rate limits, not because of "
        "its code.",
    ],
    "romanian-comma-below-7-echo-with-a-rule": [
        "Items that hit provider errors are left out of a run's score: Gemini 3.7 Flash's 100 % here covers "
        "16 of the 22 prompts, because its six guest replies hit rate limits (in task 8 it passed all six "
        "under the same rule).",
    ],
    "romanian-comma-below-8-echo-four-inputs": [
        "An empty answer counts as a failure here. Qwen 3 Next 80B Thinking used up the 8,192-token cap "
        "while thinking on 11 of its 22 cedilla prompts, so it shows 45 %; 10 of the 11 answers it finished "
        "were clean, too few to compare with other models.",
        "Grok 4.5 and Grok 4.6 show 0 % because every call returned an error, not because of their answers.",
        "Each score here is one run (the model's latest) of these 22 cedilla prompts, so differences of about "
        "20 points between two models can be chance.",
    ],
    "romanian-comma-below-10-turkish-guests": [
        "Version 2 note: version 1 counted a comma-below ș inside Romanian place names (Brașov'daki) as a "
        "Turkish word written with ș. Its single run (Gemini 3.7 Flash) failed two Turkish replies whose "
        "only comma-below letter was in Brașov, so version 2 leaves Romanian place names out of the count, "
        "as the scoring line says. The predictions are unchanged.",
        "The write-up reads the replies word by word and also treats Romanian village names (Bunești, "
        "Sâmbureștii) and dishes (papanași) as names; this task's scorer knows only the place names in its "
        "code. So 4 of the 336 Turkish replies that fail here count as correct in the write-up: under the "
        "full rule 67.9 % here and 70.5 % there, under the scoped rule 93.8 % and 94.6 %.",
    ],
    "romanian-comma-below-11-other-look-alikes": [
        "The scoring line above describes a rule per input. The code applies one rule to every answer: it "
        "passes when it has at least one Latin letter and contains neither a Cyrillic letter nor a mojibake "
        "marker (Ã or Â), whatever the input. On every stored answer the two give the same result.",
    ],
    "romanian-comma-below-13-other-wrong-letters": [
        "Erratum: input (c) above says \"Brașov becomes Braºov, țară becomes þarã\". Precisely, the cedilla "
        "spellings do: Braşov becomes Braºov and ţară becomes þarã. Windows-1250 has no ș or ț, so the task "
        "code converts the text to the cedilla first; only the example in the text is wrong.",
    ],
}

# Sentences after the last prediction that are not part of it; they get their own paragraph.
AFTER_LIST = ("Version 2 note:", "Answers that comment on the encoding")


def short_description(body: str) -> str:
    m = re.search(r'name="Romanian Comma Below [^"]*",\s*description="([^"]*)"', body)
    return m.group(1) if m else ""


def as_list(text: str, marker: str) -> list[str]:
    """Split "lead: (a) x; (b) y." before each marker like "(a) " into [lead, "(a) x;", "(b) y."]."""
    return [p.strip() for p in re.split(rf" (?={marker} )", text)]


def listify(what: str) -> str:
    """The task text with its inputs (a)-(e) and predictions (1)-(5) as lists, words unchanged."""
    k = what.find("Pre-registered predictions")
    intro, preds = (what[:k].strip(), what[k:]) if k >= 0 else (what, "")
    out = []
    parts = as_list(intro, r"\([a-e]\)")
    if len(parts) > 1:
        last, _, tail = parts[-1].partition(". ")  # the sentence after (e) is not part of it
        parts[-1] = last + "." if tail else last
        out += [parts[0], "\n".join("- " + p for p in parts[1:])] + ([tail] if tail else [])
    else:
        out.append(intro)
    if preds:
        tail = ""
        for start in AFTER_LIST:
            i = preds.find(" " + start)
            if i >= 0:
                preds, tail = preds[:i], (preds[i + 1:] + " " + tail).strip()
        parts = as_list(preds, r"\(\d\)")
        out += [parts[0], "\n".join("- " + p for p in parts[1:])] + ([tail] if tail else [])
    return "\n\n".join(out)


def words_of(text: str) -> list[str]:
    return re.sub(r"^- ", "", text, flags=re.M).split()


def block(slug: str, t: dict) -> str:
    what = listify(t["what"])
    assert words_of(what) == t["what"].split(), f"{slug}: the task text changed"
    md = build.MARKDOWN.format(title=t["title"], what=what, how=t["how"]).strip()
    body = md.split("\n", 1)[1].strip()  # drop the "# title" line
    notes = list(NOTES.get(slug, []))
    desc = short_description(t["body"])
    fixed = desc
    for ascii_text, letters in FLATTENED.items():
        fixed = fixed.replace(ascii_text, letters)
    if fixed != desc:
        notes.append("The one-line description at the top of this page comes from the task code, where "
                     f"its letters were typed in ASCII. It should read: \"{fixed}\"")
    parts = [f"## {t['title']}\nhttps://www.kaggle.com/benchmarks/tasks/danielbutnar/{slug}", body]
    if notes:
        parts.append("**Added after the runs** (not part of the text pushed with the task):\n\n"
                     + "\n".join("- " + n for n in notes))
    parts.append(f"Write-up: {WRITE_UP}\n\nCode: {REPO}/blob/main/tasks/{slug}.py "
                 f"(every model's answers: {REPO}/tree/main/results/raw/{slug})")
    return "\n\n".join(parts) + "\n"


def main():
    parts = [HEAD] + [block(slug, t) for slug, t in build.TASKS.items()]
    out = ROOT / "post" / "kaggle-task-descriptions.md"
    out.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"wrote {out.name}: {len(build.TASKS)} tasks")


if __name__ == "__main__":
    main()
