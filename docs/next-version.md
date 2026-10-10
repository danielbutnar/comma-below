# Fixes for the next task version

The task files in `tasks/` stay as they ran, so the code in this repository matches the leaderboard on Kaggle.
These are the fixes for the next version, as patches against `src/`. They are **not applied**. Each one is
listed with what it changes on the data I already have.

I tested them in a copy of the repository: with all three patches applied, `src/build.py` rebuilds the 13 tasks
and `src/dry_run.py` passes all 144 checks (the 104 it has now, plus 40 for the new fake models). The same new
fake models run against the tasks as pushed fail where they should: See and Code score 0 for `verbose`, every
task scores below 1 for `cutoff`, and every task scores 0 instead of having no score for `down`.

## What changes

1. **See scores the final answer** (`src/scoring.py`). `parse_bool` and `parse_codepoint` look in the last line
   that starts with "Answer", then in the first line, then take the last match anywhere. Rescored this way, 8
   of the 566 stored See answers (every run) change, all from wrong to right: DeepSeek-R1 goes from 30 to 36 of
   36 and Gemini 3.5 Flash-Lite from 30 to 32. No answer that passes now would fail. (A plain "last match" rule would be
   wrong: Grok 4.20 and Claude Opus 5 answer first and then mention the other code point.)
2. **An empty visible answer is missing, not wrong** (`run_items` in `src/build.py`). It is saved with the
   errors and left out of the score, as the Round 2 analysis already does (`ok_rows()` in
   `analysis/round2.py`). Qwen 3 Next 80B Thinking's task 8 score would go from 45 % to 91 % (10 of 11).
3. **A run with no completed item has no score.** Every task raises instead of returning 0.0, so a model that
   only returned errors (Grok 4.5 and 4.6, gpt-oss-120b's last Code run) shows no score rather than 0 %.
4. **Task 6 runs the model's code without the environment.** The subprocess gets only `PATH`, runs with `-I`
   (no `PYTHON*` variables, no user site) and `-X utf8`, and the harness prints its result on its own line
   after a `@@RESULT@@` tag, so code that prints without a newline can't break the parse; a bad line is caught
   as a `JSONDecodeError`. The child can still reach the network and, as the same user, read the parent's
   `/proc/<pid>/environ`; a container is the real fix. No stored item changes.
5. **Task 10 uses the write-up's name list** (`RO_NAMES`): village names (Bunești, Sâmbureștii) and Romanian
   dishes (papanași), the same list as `analysis/round2.py`. On the 336 stored Turkish replies the task's
   scorer then agrees with the write-up on every one: full rule 70.5 % (now 67.9 %), scoped rule 94.6 % (now
   93.8 %).
6. **Texts that describe what the code does.** The template says how empty answers and runs without a
   completed item count; task 4 says how the answer is found; tasks 5 and 6 get their letters back
   (peste/pește, fata/fața, French ç); task 10 mentions dishes; task 11 states the one rule the code applies.
7. **Fake models that answer like real ones** (`src/dry_run.py`): `verbose` (See answers after reasoning that
   names other code points or the opposite answer, a remark after every other answer, code that prints without
   a newline), `wrong` (the opposite See answer, so See can fail), `cutoff` (no visible answer for about half
   the prompts) and `down` (every call fails).

Not in these patches: task 13's text says "Brașov becomes Braºov, țară becomes þarã" where the cedilla spellings
do (Braşov, ţară). It is part of the pre-registered text, so I would add a version note rather than edit it.

## Applying them

Save each block below to a file and apply it from the repository root, for example
`git apply next-scoring.patch`, then:

```bash
uv run --no-project --with pandas python src/build.py
uv run --no-project --with pandas --with kaggle-benchmarks==0.6.1 python src/dry_run.py
```

Pushing the rebuilt tasks makes a new version of every task. Each needs a version note in its description, as
task 11 has, and a rerun of every model: the scores above change, and so does every run's score where an item
came back empty.

## src/scoring.py

````diff
--- a/src/scoring.py
+++ b/src/scoring.py
@@ -123,17 +123,32 @@
     return best, rest
 
 
+def final_answer(pattern, text):
+    """The one-word answer in a reply that may explain itself first.
+
+    Looks in the last line that starts with "Answer", then in the first line, then
+    takes the last match anywhere: a model that lists every code point before giving
+    its answer is scored on the answer, and one that answers first and explains
+    after is scored on its first line.
+    """
+    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
+    answer_lines = [ln for ln in lines if re.match(r"\W*answer\b", ln, re.I)]
+    for part in answer_lines[-1:] + lines[:1]:
+        m = re.search(pattern, part, re.I)
+        if m:
+            return m.group(1)
+    found = re.findall(pattern, text or "", re.I)
+    return found[-1] if found else None
+
+
 def parse_bool(text):
-    t = (text or "").strip().lower()
-    m = re.search(r"\b(true|false|yes|no)\b", t)
-    if not m:
-        return None
-    return m.group(1) in ("true", "yes")
+    word = final_answer(r"\b(true|false|yes|no)\b", text)
+    return None if word is None else word.lower() in ("true", "yes")
 
 
 def parse_codepoint(text):
-    m = re.search(r"U\+([0-9A-Fa-f]{4,6})", text or "")
-    return ("U+" + m.group(1).upper().rjust(4, "0")) if m else None
+    hexa = final_answer(r"U\+([0-9A-Fa-f]{4,6})", text)
+    return ("U+" + hexa.upper().rjust(4, "0")) if hexa else None
 
 
 def extract_python(text):
````

## src/build.py

The same one-line change replaces `return 0.0` in all 13 tasks.

````diff
--- a/src/build.py
+++ b/src/build.py
@@ -141,6 +141,7 @@
 **This task:** {what}
 
 **Scoring:** {how} Every check is done on Unicode code points after NFC normalization. No LLM judge.
+An empty visible answer counts as missing, not wrong, and a run in which no item completed has no score.
 
 This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
 data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.
@@ -236,8 +237,14 @@
         {{"item_id": r.params.get("item_id"), "message": (r.error_message or "")[-1500:]}}
         for r in runs.errored_runs
     ]
+    # An empty visible answer (a reasoning model that spent the whole token cap thinking) is a
+    # missing answer, not a wrong one: it is saved with the errors and left out of the score.
+    empty = [r for r in rows if not str(r.get("response") or "").strip()]
+    rows = [r for r in rows if str(r.get("response") or "").strip()]
+    errors += [{{"item_id": r.get("item_id"), "message": "empty visible answer"}} for r in empty]
     if errors:
-        print(len(errors), "items errored; last error:", errors[-1]["message"][-600:])
+        print(len(errors), "items errored or came back empty; last:", errors[-1]["message"][-600:])
+    print(len(rows), "items scored")
     return rows, errors
 '''
 
@@ -287,7 +294,7 @@
     save_rows("romanian-comma-below-1-write", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df[["item_id", "kind", "pass", "knows_spelling", "comma", "cedilla", "missing"]].to_string())
     return float(df["pass"].mean()) if len(df) else 0.0
 ''',
@@ -336,7 +343,7 @@
     save_rows("romanian-comma-below-2-echo", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("variant")[["pass", "comma", "cedilla"]].mean().to_string())
     ced = df[df["variant"] == "cedilla"]
     return float(ced["pass"].mean()) if len(ced) else 0.0
@@ -381,7 +388,7 @@
     save_rows("romanian-comma-below-3-fix", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("level")[["pass", "typo_fixed", "cedilla"]].mean().to_string())
     return float(df["pass"].mean()) if len(df) else 0.0
 ''' % (I.FIX_LEVELS,),
@@ -393,7 +400,8 @@
     "can the model perceive the difference? Three probes: are two strings identical (8 differ only by "
     "comma vs cedilla or visibly, 8 are identical), does a sentence contain cedilla letters (6 yes, 6 no), "
     "and which code point sits at a given position (4 comma, 4 cedilla).",
-    "exact answer match (true/false, or U+XXXX). Score = accuracy over all 36 items; "
+    "the final answer must match: the last line that starts with Answer, else the first line, else the "
+    "last true/false or U+XXXX in the reply. Score = accuracy over all 36 items; "
     "a coin flip scores about 0.5 on the first two probes.",
     "ITEMS", data_see(),
     '''
@@ -419,7 +427,7 @@
     save_rows("romanian-comma-below-4-see", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby(["kind", "note"])["pass"].mean().to_string())
     return float(df["pass"].mean()) if len(df) else 0.0
 ''',
@@ -452,13 +460,13 @@
 
 
 @kbench.task(name="Romanian Comma Below 5: Restore",
-             description="Restore Romanian diacritics where context decides (peste/peste, fata/fata). Letter-exact, no judge.")
+             description="Restore Romanian diacritics where context decides (peste/pește, fata/fața). Letter-exact, no judge.")
 def romanian_comma_below_5_restore(llm) -> float:
     rows, errors = run_items(restore_item, llm, pd.DataFrame(ITEMS))
     save_rows("romanian-comma-below-5-restore", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df[["item_id", "pass", "pass_if_cedilla_ok", "word_accuracy", "cedilla"]].to_string())
     return float(df["pass"].mean()) if len(df) else 0.0
 ''',
@@ -489,7 +497,7 @@
     res["idempotent"] = isinstance(once, str) and f(once) == once
 except BaseException:
     res["idempotent"] = False
-print(json.dumps(res))
+print("\n@@RESULT@@" + json.dumps(res))
 '''
 
 task(
@@ -509,15 +517,19 @@
 def code_item(llm, item_id: str, prompt: str) -> dict:
     response = ask(llm, prompt)
     code = extract_python(response)
-    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
+    # The model's code gets no API keys: only PATH; -I ignores PYTHON* variables and the user site.
+    env = {"PATH": os.environ.get("PATH", "")}
     try:
-        proc = subprocess.run([sys.executable, "-c", HARNESS, json.dumps(DATA["tests"])],
+        proc = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", HARNESS, json.dumps(DATA["tests"])],
                               input=code, capture_output=True, text=True, encoding="utf-8",
                               timeout=30, env=env)
-        lines = proc.stdout.strip().splitlines()
-        res = json.loads(lines[-1]) if lines else {"load_error": proc.stderr[-300:]}
+        tagged = [ln for ln in proc.stdout.splitlines() if ln.startswith("@@RESULT@@")]
+        res = (json.loads(tagged[-1][len("@@RESULT@@"):]) if tagged
+               else {"load_error": (proc.stdout + proc.stderr)[-300:]})
     except subprocess.TimeoutExpired:
         res = {"load_error": "timeout"}
+    except json.JSONDecodeError:
+        res = {"load_error": "bad harness output"}
     names = [t[0] for t in DATA["tests"]] + ["idempotent"]
     passed = [n for n in names if res.get(n) is True]
     score = len(passed) / len(names)
@@ -528,13 +540,13 @@
 
 
 @kbench.task(name="Romanian Comma Below 6: Code",
-             description="Write fix_romanian(text) to repair cedilla letters; 14 hidden tests incl. uppercase, decomposed forms, French c.")
+             description="Write fix_romanian(text) to repair cedilla letters; 14 hidden tests incl. uppercase, decomposed forms, French ç.")
 def romanian_comma_below_6_code(llm) -> float:
     rows, errors = run_items(code_item, llm, pd.DataFrame(DATA["prompts"]))
     save_rows("romanian-comma-below-6-code", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df[["item_id", "score", "failed", "load_error"]].to_string())
     return float(df["score"].mean()) if len(df) else 0.0
 ''' % (HARNESS,),
@@ -584,7 +596,7 @@
     save_rows("romanian-comma-below-7-echo-with-a-rule", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("kind")[["pass", "comma", "cedilla"]].mean().to_string())
     return float(df["pass"].mean())
 ''' % (I.ECHO_SYSTEM, I.ECHO_SUMMARY, I.ECHO_RAG_PROMPT, ECHO_RULE),
@@ -749,7 +761,7 @@
     save_rows("romanian-comma-below-8-echo-four-inputs", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("variant")[["pass", "comma", "cedilla", "st_total", "st_cedilla", "st_ascii"]].mean().to_string())
     ced = df[df["variant"] == "cedilla"]
     return float(ced["pass"].mean()) if len(ced) else 0.0
@@ -800,7 +812,7 @@
     save_rows("romanian-comma-below-9-contagion", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("cond")[["pass", "comma", "cedilla"]].mean().to_string())
     return float(df["pass"].mean())
 ''',
@@ -817,9 +829,9 @@
     "(2) task 7's rule makes some models write Turkish with the Romanian comma letter; (3) the scoped "
     "rule keeps Turkish intact and still fixes Romanian.",
     "a Turkish reply passes when its Turkish words contain the Turkish ş and never the comma-below ș "
-    "(Romanian place names such as Brașov are left out of the count: either spelling is defensible "
-    "there); a Romanian reply passes when it has zero cedilla or look-alike letters and at least one "
-    "comma-below letter. Score = pass rate over all 36 items.",
+    "(Romanian place names such as Brașov and dishes such as papanași are left out of the count: either "
+    "spelling is defensible there); a Romanian reply passes when it has zero cedilla or look-alike "
+    "letters and at least one comma-below letter. Score = pass rate over all 36 items.",
     "ITEMS", data_turkish(),
     '''
 S_CEDILLA = (chr(0x15E), chr(0x15F))
@@ -829,8 +841,11 @@
                        0x219: "s", 0x218: "S", 0x21B: "t", 0x21A: "T", 0x15F: "s", 0x15E: "S",
                        0x163: "t", 0x162: "T"})
 # Romanian place names a Turkish reply may quote: either s letter is defensible inside them.
-RO_NAMES = ("brasov", "rasnov", "timisoara", "iasi", "bucuresti", "sighisoara", "mures", "arges",
-            "constanta", "pitesti", "cismigiu", "transfagarasan", "romania")
+RO_NAMES = ("brasov", "rasnov", "bunesti", "sambures", "timisoara", "iasi", "bucuresti", "sighisoara", "mures",
+            "arges", "constanta", "pitesti", "cismigiu", "transfagarasan", "romania",
+            # Romanian dishes a reply may offer (papanasi), the same list as analysis/round2.py
+            "papanas", "mamalig", "ciorb", "sarmal", "cozonac", "mititei", "zacusc", "bulz", "placint",
+            "tochitur", "pastram", "tuica", "palinc")
 
 
 def turkish_counts(text):
@@ -871,7 +886,7 @@
     save_rows("romanian-comma-below-10-turkish-guests", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby(["lang", "rule"])[["pass", "s_cedilla", "s_comma"]].mean().to_string())
     return float(df["pass"].mean())
 ''',
@@ -925,8 +940,8 @@
     "replaced, versus about 2 % for the Romanian cedilla). Its single run (Gemini 3.7 Flash) copied none "
     "of it, so version 2 adds look-alikes confined to the names, the same words mojibake touches. The "
     "predictions are unchanged.",
-    "a clean or Cyrillic-input answer passes when it contains no Cyrillic letter; a mojibake-input answer "
-    "passes when it contains no mojibake marker (Ã or Â). Score = pass rate over all 48 items.",
+    "an answer passes when it has at least one Latin letter and contains neither a Cyrillic letter nor a "
+    "mojibake marker (Ã or Â), whatever the input. Score = pass rate over all 48 items.",
     "ITEMS", data_lookalike(),
     '''
 MOJIBAKE_MARKERS = (chr(0xC3), chr(0xC2))
@@ -959,7 +974,7 @@
     save_rows("romanian-comma-below-11-other-look-alikes", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby(["variant", "kind"])[["pass", "cyrillic", "mojibake"]].mean().to_string())
     return float(df["pass"].mean())
 ''',
@@ -1003,7 +1018,7 @@
     save_rows("romanian-comma-below-12-turns", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     print(df.groupby("cond")[["pass", "first_cedilla", "second_cedilla"]].mean().to_string())
     return float(df["pass"].mean())
 ''',
@@ -1174,7 +1189,7 @@
     save_rows("romanian-comma-below-13-other-wrong-letters", llm, rows, errors)
     df = pd.DataFrame(rows)
     if df.empty:
-        return 0.0
+        raise RuntimeError("no item completed (provider errors or empty answers): this run has no score")
     cols = ["pass", "sl_st", "sl_st_comma", "sl_st_cedilla", "sl_st_dot", "sl_st_legacy", "sl_st_bare",
             "sl_a", "sl_a_breve", "sl_a_tilde"]
     print(df.groupby("variant")[cols].mean().to_string())
````

## src/dry_run.py

````diff
--- a/src/dry_run.py
+++ b/src/dry_run.py
@@ -13,10 +13,14 @@
   flaky    - fails the first call for each prompt with a 429, so the retry is tested
   picky    - rejects max_completion_tokens and checks the 8,192-token cap, so the fallback is tested
   thinker  - the gold answer after a <think> block that contains cedilla letters
-Tasks 1-7 run against seven of them (perfect, cedilla, strip, mirror, flaky, picky, thinker),
-tasks 8-12 add sticky and normalizer (nine), and task 13 adds legacyreader (ten).
-The expected scores are asserted, so a scoring bug fails loudly. The fake models answer in the
-format the prompt asks for, so the parsers are not tested on wordy answers (docs/next-version.md).
+  verbose  - the gold answer the way real models wrap it: See answers after reasoning that names
+             other code points or the opposite answer, a remark after every other answer, and code
+             that prints without a newline when it is loaded
+  wrong    - the opposite See answer (true/false and comma/cedilla code points swapped)
+  cutoff   - no visible answer (an unclosed <think>) for about half the prompts, gold for the rest
+  down     - every call fails with a 404, so no item completes and the run has no score
+Every task also runs against verbose, cutoff and down; task 4 also against wrong.
+The expected scores are asserted, so a scoring bug fails loudly.
 
 Usage:  uv run --no-project --with pandas --with kaggle-benchmarks==0.6.1 python src/dry_run.py [-8- -9- ...]
         (a fragment of a task name runs only the matching tasks)
@@ -49,6 +53,9 @@
     text = unicodedata.normalize("NFC", text)
     return text.translate(str.maketrans({"ş": "ș", "Ş": "Ș", "ţ": "ț", "Ţ": "Ț"}))
 ```'''
+CHATTY_CODE = ("Here is the function:\n\n"
+               + GOOD_CODE.replace("import unicodedata\n", 'import unicodedata\nprint("ready", end="")\n')
+               + "\n\nIt also handles decomposed letters.")
 NAIVE_CODE = '''```python
 def fix_romanian(text):
     return text.replace("ş", "ș").replace("ţ", "ț")
@@ -103,6 +110,19 @@
 ORACLE = oracle()
 
 
+FLIP = {"true": "false", "false": "true", "U+0219": "U+015F", "U+015F": "U+0219",
+        "U+021B": "U+0163", "U+0163": "U+021B", "U+021A": "U+0162", "U+0162": "U+021A"}
+
+
+def chatty(gold: str) -> str:
+    """The gold answer wrapped the way real models wrap it."""
+    if gold in ("true", "false"):
+        return f"At first sight {FLIP[gold]}, but the code points settle it.\n\nAnswer: {gold}"
+    if gold.startswith("U+"):
+        return f"The letters, in order:\n1. 'B' (U+0042)\n2. 'r' (U+0072)\n\nThe code point asked for is **{gold}**."
+    return gold + "\n\nHope this helps."
+
+
 def corrupt_like(prompt: str, text: str) -> str:
     """Apply to `text` the corruption found in `prompt` (cedilla, dot below, old Romanian mojibake,
     Cyrillic look-alikes, UTF-8 mojibake)."""
@@ -135,6 +155,10 @@
             if "max_completion_tokens" in kwargs:
                 raise TypeError("create() got an unexpected keyword argument 'max_completion_tokens'")
             assert kwargs.get("max_tokens") == 8192, kwargs
+        if self.policy == "down":
+            raise RuntimeError("Error code: 404 - model not found")
+        if self.policy == "cutoff" and sum(map(ord, prompt)) % 2 == 0:
+            return LLMResponse(content="<think>The input has cedilla letters, so")
         if self.policy == "flaky":
             assert not_duplicated, f"retry duplicated the question: {len(users)} user messages"
             if prompt not in self.seen:
@@ -144,7 +168,7 @@
         if gold is None:
             raise KeyError(f"no oracle answer for prompt: {prompt[:80]!r}")
         if gold == "CODE":
-            return LLMResponse(content=NAIVE_CODE if self.policy == "cedilla" else GOOD_CODE)
+            return LLMResponse(content={"cedilla": NAIVE_CODE, "verbose": CHATTY_CODE}.get(self.policy, GOOD_CODE))
         p = self.policy
         if p == "cedilla":
             out = I.to_cedilla(gold)
@@ -159,6 +183,10 @@
             out = I.to_cedilla(gold) if LEGACY & set(prompt) else gold
         elif p == "strip":
             out = I.strip_diacritics(gold)
+        elif p == "verbose":
+            out = chatty(gold)
+        elif p == "wrong":
+            out = FLIP.get(gold, gold)
         else:
             out = gold
         if p == "thinker":
@@ -177,20 +205,33 @@
 
 EXPECT = {
     # task: {policy: expected score}
-    "romanian-comma-below-1-write": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-2-echo": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-7-echo-with-a-rule": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-3-fix": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-4-see": {"perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-5-restore": {"perfect": 1.0, "cedilla": None, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-6-code": {"perfect": 1.0, "cedilla": None, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
+    "romanian-comma-below-1-write": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-2-echo": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-7-echo-with-a-rule": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-3-fix": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-4-see": {"wrong": 0.0, "perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-5-restore": {"perfect": 1.0, "cedilla": None, "strip": 0.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-6-code": {"perfect": 1.0, "cedilla": None, "strip": 1.0, "mirror": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
     # Round 2
-    "romanian-comma-below-8-echo-four-inputs": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-9-contagion": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.2, "sticky": 0.2, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-10-turkish-guests": {"perfect": 1.0, "cedilla": 2 / 3, "strip": 2 / 3, "mirror": 2 / 3, "sticky": 2 / 3, "normalizer": 1 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-11-other-look-alikes": {"perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 0.25, "sticky": 0.25, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-12-turns": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 2 / 3, "sticky": 1 / 3, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
-    "romanian-comma-below-13-other-wrong-letters": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "legacyreader": 2 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0},
+    "romanian-comma-below-8-echo-four-inputs": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-9-contagion": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.2, "sticky": 0.2, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-10-turkish-guests": {"perfect": 1.0, "cedilla": 2 / 3, "strip": 2 / 3, "mirror": 2 / 3, "sticky": 2 / 3, "normalizer": 1 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-11-other-look-alikes": {"perfect": 1.0, "cedilla": 1.0, "strip": 1.0, "mirror": 0.25, "sticky": 0.25, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-12-turns": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 2 / 3, "sticky": 1 / 3, "normalizer": 1.0, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
+    "romanian-comma-below-13-other-wrong-letters": {"perfect": 1.0, "cedilla": 0.0, "strip": 0.0, "mirror": 0.0, "sticky": 0.0, "normalizer": 1.0, "legacyreader": 2 / 3, "flaky": 1.0, "picky": 1.0, "thinker": 1.0,
+        "verbose": 1.0, "cutoff": 1.0, "down": "no score"},
 }
 
 
@@ -206,9 +247,17 @@
         ns = load_task(slug)
         func = ns[slug.replace("-", "_")]
         for policy, want in expect.items():
-            run = func.run(FakeLLM(policy))
-            got = run.result
-            status = "ok" if want is None or abs(got - want) < 1e-9 else "FAIL"
+            try:
+                got = func.run(FakeLLM(policy)).result
+            except RuntimeError as e:  # a run with no completed item raises instead of scoring 0
+                if "no item completed" not in str(e):
+                    raise
+                got = None
+            if want == "no score" or got is None:
+                status = "ok" if want == "no score" and got is None else "FAIL"
+                got = float("nan") if got is None else got
+            else:
+                status = "ok" if want is None or abs(got - want) < 1e-9 else "FAIL"
             if status == "FAIL":
                 failures.append((slug, policy, got, want))
             print(f"{slug:22s} {policy:8s} score={got:.3f} expected={want} {status}")
````
