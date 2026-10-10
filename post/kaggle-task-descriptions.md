# Kaggle task descriptions

Paste one block into each task's Description field on Kaggle:

1. Open the task page (the link under each heading) and edit its Description.
2. Copy the block from "Part of **Comma Below**" down to the "Code:" line and paste it as Markdown.
3. Save, then open the page in a logged-out window to check that it shows.

Each block is the first cell of that task's notebook, generated from src/build.py by
post/task_descriptions.py. The pre-registered predictions are word for word as pushed before the runs;
only the layout differs (they, and task 13's five inputs, are shown as lists). The notes under "Added
after the runs" were written after the runs and are not part of the pushed text.

## Romanian Comma Below 1: Write
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-1-write

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** English prompts ask for Romanian text (translations with ASCII place names, single words, capitals, JSON, JavaScript, HTML, longer copy). Does the model write the correct letters?

**Scoring:** an item passes when the answer has zero cedilla or look-alike letters and every required word (for example *Timișoara*) appears code-point exact (case-insensitive); items without required words must contain at least one comma-below letter. Score = share of items passed. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-1-write.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-1-write)

## Romanian Comma Below 2: Echo
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-2-echo

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** the same Romanian guest messages and news paragraphs arrive twice: once typed correctly and once typed with cedilla letters. The model replies to the guest, summarizes the paragraph, or answers a question from it (retrieval style), always in Romanian. Does it copy the user's wrong letters?

**Scoring:** a reply passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate on the **cedilla** inputs; the clean inputs are the control (saved in the results file). Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-2-echo.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-2-echo)

## Romanian Comma Below 3: Fix
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-3-fix

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** six Romanian texts typed with cedilla letters, each with one ordinary typo, and three instructions: a plain *proofread*, *correct the spelling and the diacritics*, and an explicit description of the cedilla problem. Does the model repair the letters, and does it need to be told?

**Scoring:** the rewritten text (the paragraph closest to the answer key; a changelog after it is ignored) passes when it has zero cedilla or look-alike letters and contains every gold word that has a comma-below letter. The typo fix is recorded separately. Score = share of answers passed. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-3-fix.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-3-fix)

## Romanian Comma Below 4: See
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-4-see

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** can the model perceive the difference? Three probes: are two strings identical (8 differ only by comma vs cedilla or visibly, 8 are identical), does a sentence contain cedilla letters (6 yes, 6 no), and which code point sits at a given position (4 comma, 4 cedilla).

**Scoring:** exact answer match (true/false, or U+XXXX). Score = accuracy over all 36 items; a coin flip scores about 0.5 on the first two probes. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- The scorer takes the first true/false or U+XXXX in each answer, so "exact answer match" above means that first match. The prompts ask for the answer alone, and most models give it that way. DeepSeek-R1 listed every letter's code point before giving the right one, so its six code-point answers count as wrong here: it shows 83 %, and scored on its final answers it gets 36 of 36. Gemini 3.5 Flash-Lite shows 83 % and gets 32 of 36 on its final answers. No other model changes.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-4-see.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-4-see)

## Romanian Comma Below 5: Restore
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-5-restore

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** 30 Romanian sentences typed without diacritics; the model puts them back. Several sentences only differ by context (*peste* over / *pește* fish, *fata* girl / *fața* face, *masa* / *masă*).

**Scoring:** a sentence passes when every word matches the gold letter for letter (case and punctuation ignored). Score = share of sentences passed. The results file also records whether the sentence would pass if cedilla letters were accepted, which separates language knowledge from encoding. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- The one-line description at the top of this page comes from the task code, where its letters were typed in ASCII. It should read: "Restore Romanian diacritics where context decides (peste/pește, fata/fața). Letter-exact, no judge."

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-5-restore.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-5-restore)

## Romanian Comma Below 6: Code
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-6-code

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** the model writes `fix_romanian(text)`, a Python function that repairs cedilla letters. Two prompt phrasings (one names every letter, one only gives the goal). Hidden tests cover lowercase and uppercase, decomposed forms (s + U+0327), text that is already correct, French ç that must not change, whitespace and emoji, and idempotence.

**Scoring:** share of the 14 hidden tests passed, averaged over the two prompts. The code runs in a subprocess with a 30 s timeout. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- Items that hit provider errors are left out of a run's score, and a run with no completed item scores 0: gpt-oss-120b's latest run shows 0 because both prompts hit rate limits, not because of its code.
- The one-line description at the top of this page comes from the task code, where its letters were typed in ASCII. It should read: "Write fix_romanian(text) to repair cedilla letters; 14 hidden tests incl. uppercase, decomposed forms, French ç."

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-6-code.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-6-code)

## Romanian Comma Below 7: Echo With a Rule
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-7-echo-with-a-rule

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** the cedilla inputs of task 2 (Echo) again, with one added sentence in the system prompt: *Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them.* Does the obvious fix work?

**Scoring:** same as Echo: an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate; compare with the cedilla column of task 2. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- Items that hit provider errors are left out of a run's score: Gemini 3.7 Flash's 100 % here covers 16 of the 22 prompts, because its six guest replies hit rate limits (in task 8 it passed all six under the same rule).

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-7-echo-with-a-rule.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-7-echo-with-a-rule)

## Romanian Comma Below 8: Echo, Four Inputs
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-8-echo-four-inputs

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** task 2's 22 prompts (guest replies, news summaries, retrieval-style answers) under four inputs: typed correctly, typed with cedilla letters, typed without any diacritics (ASCII), and typed with cedilla plus task 7's one-sentence rule in the system prompt. Run on every model Kaggle serves, so model generations and sizes can be compared on identical items.

Pre-registered predictions (written before any run):

- (1) clean input stays near 100 % for every model;
- (2) cedilla input fails far more often than ASCII input, because a missing diacritic looks broken and a cedilla does not;
- (3) newer models in a family copy the cedilla at least as often as older ones;
- (4) the rule lifts cedilla input to at least 90 % for most models.

**Scoring:** an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate on the **cedilla** inputs (as in task 2). The results file also records, for every answer, how each s/t word of the source was spelled (comma, cedilla, or no diacritic). Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- An empty answer counts as a failure here. Qwen 3 Next 80B Thinking used up the 8,192-token cap while thinking on 11 of its 22 cedilla prompts, so it shows 45 %; 10 of the 11 answers it finished were clean (91 %, the figure the write-up uses).
- Grok 4.5 and Grok 4.6 show 0 % because every call returned an error, not because of their answers.
- Each model ran once on these 22 cedilla prompts, so differences of about 20 points between two models can be chance.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-8-echo-four-inputs.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-8-echo-four-inputs)

## Romanian Comma Below 9: Contagion
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-9-contagion

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** four Romanian news paragraphs as documents and one question about one of them, answered in Romanian. Five conditions per question: everything clean; the target clean and one or all three other documents typed with cedilla; the target typed with cedilla and the others clean; everything typed with cedilla. When the target is clean, any cedilla letter in the answer came from somewhere else.

Pre-registered predictions (written before any run):

- (1) with a clean target, the answer stays clean for most models even when the other three documents are cedilla, because answers reuse the target's words;
- (2) the models that rewrote whole answers in cedilla in task 2 are the ones whose clean-target answers get infected;
- (3) a cedilla target is copied less when the other documents are clean.

**Scoring:** an answer passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate over all 40 items. Every cedilla word in an answer is traced to the target document, another document, or neither. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-9-contagion.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-9-contagion)

## Romanian Comma Below 10: Turkish Guests
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-10-turkish-guests

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** the cedilla letter is wrong in Romanian and right in Turkish (*teşekkür*, *şehir*). Eight Turkish guest messages are answered with no rule, with task 7's rule (*never ş or ţ*), and with a rule scoped to Romanian; six Romanian messages typed with cedilla are answered under both rules. Does the fix for Romanian break Turkish?

Pre-registered predictions (written before any run):

- (1) without a rule, Turkish replies keep ş;
- (2) task 7's rule makes some models write Turkish with the Romanian comma letter;
- (3) the scoped rule keeps Turkish intact and still fixes Romanian.

**Scoring:** a Turkish reply passes when its Turkish words contain the Turkish ş and never the comma-below ș (Romanian place names such as Brașov are left out of the count: either spelling is defensible there); a Romanian reply passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate over all 36 items. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- Version 2 note: version 1 counted a comma-below ș inside Romanian place names (Brașov'daki) as a Turkish word written with ș. Its single run (Gemini 3.7 Flash) failed two Turkish replies whose only comma-below letter was in Brașov, so version 2 leaves Romanian place names out of the count, as the scoring line says. The predictions are unchanged.
- The write-up reads the replies word by word and also treats Romanian village names (Bunești, Sâmbureștii) and dishes (papanași) as names; this task's scorer knows only the place names in its code. So 4 of the 336 Turkish replies that fail here count as correct in the write-up: under the full rule 67.9 % here and 70.5 % there, under the scoped rule 93.8 % and 94.6 %.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-10-turkish-guests.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-10-turkish-guests)

## Romanian Comma Below 11: Other Look-Alikes
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-11-other-look-alikes

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** the Echo design outside Romanian. Six English news paragraphs with accented names (Zürich, Café Müller, Málaga) are summarized or used to answer a question, typed four ways: correctly; with Cyrillic look-alike letters (а с е о р for a c e o p) in every word; with Cyrillic look-alikes only inside the accented names; and as mojibake in the same names (UTF-8 read as Windows-1252, *ZÃ¼rich*), which looks broken.

Pre-registered predictions (written before any run):

- (1) clean input stays near 100 %;
- (2) Cyrillic look-alikes are copied into answers far more often than mojibake, because mojibake looks broken and look-alikes do not;
- (3) the models that copy the Romanian cedilla most (task 8) also copy the Cyrillic look-alikes most.

Version 2 note: version 1 had only the dense Cyrillic variant (about a third of all letters replaced, versus about 2 % for the Romanian cedilla). Its single run (Gemini 3.7 Flash) copied none of it, so version 2 adds look-alikes confined to the names, the same words mojibake touches. The predictions are unchanged.

**Scoring:** a clean or Cyrillic-input answer passes when it contains no Cyrillic letter; a mojibake-input answer passes when it contains no mojibake marker (Ã or Â). Score = pass rate over all 48 items. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- The scoring line above describes a rule per input. The code applies one rule to every answer: it passes when it has at least one Latin letter and contains neither a Cyrillic letter nor a mojibake marker (Ã or Â), whatever the input. On every stored answer the two give the same result.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-11-other-look-alikes.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-11-other-look-alikes)

## Romanian Comma Below 12: Turns
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-12-turns

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** two news summaries in one chat. The second summary is scored: after a first text typed with cedilla, is the summary of a clean second text still written with cedilla? After a clean first text, is a cedilla second text copied less than in task 2?

Pre-registered predictions (written before any run):

- (1) a cedilla first turn infects some clean second summaries, mostly for models whose first summary was itself in cedilla;
- (2) a clean first turn does not protect a cedilla second text much.

**Scoring:** the second summary passes when it has zero cedilla or look-alike letters and at least one comma-below letter. Score = pass rate of the second summaries over all 18 conversations. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-12-turns.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-12-turns)

## Romanian Comma Below 13: Other Wrong Letters
https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-13-other-wrong-letters

Part of **Comma Below**, a benchmark on one Romanian letter pair: ș ț (s and t with a comma below,
U+0219 and U+021B, the correct Romanian letters) versus ş ţ (s and t with a cedilla, U+015F and U+0163),
a legacy encoding error that still fills the Romanian web. They look almost identical and are different
characters: search, sorting, spell-check and screen readers treat them differently.

**This task:** task 8's 16 prompts where models reuse the source's words (6 news summaries and 10 questions about a document, built on 8 source texts), with the source typed five ways:

- (a) with the cedilla, as in task 8 (the control);
- (b) with s and t with a dot below (ṣ ṭ): near-identical to the right letters and real letters elsewhere (Yoruba, transliteration), but not used in Romanian;
- (c) as the old mojibake of Romanian web pages and subtitles (Windows-1250 bytes read as Windows-1252: Brașov becomes Braºov, țară becomes þarã), which also turns ă into ã;
- (d) with the cedilla and task 10's scoped rule in the system prompt;
- (e) with the cedilla and task 7's full rule, for a same-run comparison with (d).

Every s/t letter of the source's words is scored in the answer as kept in the input's form, comma below (right), cedilla, or bare; ă is scored apart.

Pre-registered predictions (written before any run; new runs on the same 16 prompts):

- (1) Main test: the dot below is kept in a smaller share of s/t letters than the cedilla, on the same models and prompts (paired difference, 95 % interval below zero). Kept about as often would mean any letter-like substitute gets copied; kept less often, that the familiar wrong spelling is what gets kept.
- (2) The old mojibake is kept less often than the cedilla; kept about as often would mean models copy whatever the input has. Romanian mojibake looks rare in training text (no tokenizer merges for it), so here 'seen in Romanian text' and 'the cedilla is special' predict the same result.
- (3) Repaired dot-below and mojibake letters become comma-below letters, not the cedilla, in at least 90 % of cases.
- (4) Both rules give at least 90 % clean answers, and the scoped rule is within 5 points of the full rule.
- (5) Replication of task 8: in cedilla answers that keep every cedilla of the input, at least 80 % of the s/t words the model adds itself (not in the source and not inflections of source words: no shared start of 5 letters) have the cedilla; in answers that keep only some, at most 30 %.

Answers that comment on the encoding are flagged and reported with and without; answers with none of the source's s/t words count as no data.

**Scoring:** an answer passes when it has no cedilla, dot-below, mojibake (º ª þ Þ) or look-alike (ã ǎ) letters and at least one comma-below letter. Score = pass rate on the three wrong-letter inputs without a rule (a, b, c). The results file records, for every answer, each s/t and ă letter of the source's words as written (slot counts), the word-level forms as in task 8, the wrong-form words and which of them were copied from the input, and the words with which an answer comments on the encoding. Every check is done on Unicode code points after NFC normalization. No LLM judge.

This source file is ASCII-only on purpose (Romanian letters are escapes) and verifies a SHA-256 of its
data before running, so no editor, CLI or notebook conversion can silently swap the letters under test.

**Added after the runs** (not part of the text pushed with the task):

- Erratum: input (c) above says "Brașov becomes Braºov, țară becomes þarã". Precisely, the cedilla spellings do: Braşov becomes Braºov and ţară becomes þarã. Windows-1250 has no ș or ț, so the task code converts the text to the cedilla first; only the example in the text is wrong.

Write-up: https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

Code: https://github.com/danielbutnar/comma-below/blob/main/tasks/romanian-comma-below-13-other-wrong-letters.py (every model's answers: https://github.com/danielbutnar/comma-below/tree/main/results/raw/romanian-comma-below-13-other-wrong-letters)
