Romanian writes **ș** and **ț** with a comma below (U+0219, U+021B). In the 1990s the common encodings had no such letters, so Romanian text used the look-alike **ş** and **ţ** with a cedilla (U+015F, U+0163). On 30 September 2026, 29 of 35 Romanian front pages I checked (government, National Bank, Brașov city hall, rail operator, news sites) still had cedilla letters in Romanian words.

The two look almost identical and are different characters: `==`, `grep`, SQL with a binary collation, site search, deduplication and URL slugs treat them as two words.

**What it found.** I gave 43 models the same 22 Romanian prompts typed four ways (task 8). Typed correctly, 99 % of the answers came back clean; typed without any diacritics, 96 %; typed with the cedilla letters, 68 %. The models put missing letters back but keep wrong ones, and not only in the words they copy: when an answer kept all of my cedillas, 95 % of the new ș/ț words the model chose itself had the cedilla too, against 9.5 % when it kept only some. I call it the keyboard echo. It is specific to the cedilla: on 28 models (task 13), the same texts typed with a dot below (Braṣov) or as old mojibake (Braºov) kept 0.9 % and 1.4 % of those letters, against 38 % for the cedilla. One sentence in the system prompt lifts cedilla input to 95 % clean, and breaks Turkish, where ş is the right letter: on 14 models, correct Turkish replies fell from 100 % to 71 %, and came back to 95 % when the rule said it applies to Romanian only (task 10).

Try it yourself: the [cedilla checker](https://danielbutnar.github.io/comma-below/post/checker.html) marks every cedilla letter in a model's answer, and the [two-minute human test](https://danielbutnar.github.io/comma-below/human/test.html) asks whether you can tell ş from ș.

**Write-up:** [Braşov or Brașov? on DEV](https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a)

**Code, raw answers, analysis and a claim checker:** https://github.com/danielbutnar/comma-below

Every score is computed from Unicode code points after NFC normalization; there is no LLM judge. I'm a native Romanian speaker and checked the answer keys myself. Every task was first run against fake models with known behaviour (seven on tasks 1–7, nine on tasks 8–12, ten on task 13) and their expected scores asserted.

| # | Task | What it measures |
| --- | --- | --- |
| 1 | Write | From English prompts with ASCII place names, does the model write ș/ț? |
| 2 | Echo | The same guest messages and news paragraphs, typed correctly and typed with cedilla. Does the reply, summary or document answer copy the wrong letters? Score = pass rate on the cedilla inputs. |
| 3 | Fix | Cedilla text plus one typo, under "proofread", "correct the spelling and the diacritics", and an explicit instruction. |
| 4 | See | Same/different pairs (half byte-identical), cedilla detection in a sentence, code point at a position. |
| 5 | Restore | Put diacritics back where only context decides (peste/pește, fata/fața). |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests (uppercase, decomposed s + U+0327, French ç). |
| 7 | Echo + rule | Echo's cedilla inputs with one system-prompt sentence asking for comma-below letters. |
| 8 | Echo, four inputs | Echo's 22 prompts typed correctly, with cedilla, without diacritics, and with cedilla + the rule; every model Kaggle serves. Score = pass rate on the cedilla inputs. |
| 9 | Contagion | Four documents, a question about one; 0, 1 or 3 of the others typed with cedilla, or the target itself. |
| 10 | Turkish guests | Turkish (ş is correct there) under no rule, task 7's rule, and the same rule scoped to Romanian. |
| 11 | Other look-alikes | English text typed with Cyrillic look-alike letters (а с е о р) in every word or only in the names, or as mojibake (ZÃ¼rich). |
| 12 | Turns | Two summaries in one chat: does a cedilla first text change the second? |
| 13 | Other wrong letters | Task 8's summaries and document questions typed with a dot below (Braṣov) or as old Windows-1250 mojibake (Braºov) instead of the cedilla, and with the scoped and the full rule. |

Tasks 8–13 carry predictions written before their first run. They are in the first cell of each task's notebook, and the task's version history on Kaggle shows when each version was pushed. Tasks 10 and 11 had a pilot run on one model and a second version after it (task 10 stopped counting ș inside Romanian place names, task 11 added look-alikes confined to the names); their descriptions say what changed, and the predictions are unchanged.

**Reading the leaderboard**

- Write is close to 100 % for every model but one (85–100 %). See (71–100 %) and Fix (72–100 %) are not controls: Claude Haiku 4.5, Claude Opus 5, Claude Sonnet 5 and Gemini 3.8 Flash called all six byte-identical pairs of Romanian words different, and Claude Sonnet 5 fixed 1 of 6 cedilla texts when only asked to proofread.
- The overall score averages different tasks for different models: 15 models ran the first seven tasks, 10 to 28 ran the follow-up tasks 9–13, and every model ran task 8. To compare models, read task 8.
- Task 8's leaderboard ranks the models on the copying itself: the share of clean answers when the input has cedillas. An empty answer counts as a failure there. Qwen 3 Next 80B Thinking used up the 8,192-token cap while thinking on 11 of its 22 cedilla prompts, so it shows 45 %; 10 of the 11 answers it finished were clean (91 %, the figure the write-up uses). Grok 4.5 and Grok 4.6 show 0 % because every call returned an error. Each model ran task 8 once, on 22 cedilla prompts, so differences of about 20 points between two models can be chance.
- See counts the first true/false or U+XXXX in each answer. DeepSeek-R1 listed every letter's code point before giving the right one, so it shows 83 % with all 36 answers right (Gemini 3.5 Flash-Lite shows 83 % with 32 of 36 right).

**Notes on method**

- Output is capped at 8,192 tokens per call. Answers are scored on their visible text; inline `<think>` reasoning is removed first.
- Models reached through the OpenAI-compatible proxy run at the provider's default temperature; a call retried after a provider error runs at temperature 0 with seed 0. The write-up reports Echo as the mean of all runs on the same prompts (tasks 2 and 8): four for 14 of the 15 first-round models, three for GPT-6 Astra, whose task 8 runs failed. The leaderboard shows each model's latest run.
- Items that hit provider errors are left out of a run's score, and a run with no completed item scores 0. Grok 4.5 and Grok 4.6 are listed by Kaggle but returned errors on every call. gpt-oss-120b's provider was overloaded during the first round, so its first-round scores rest on as few as 7 of 36 items (See), and its latest Code run shows 0 because both prompts hit rate limits.
- Task source files are ASCII-only and verify a SHA-256 of their data before running, because the Kaggle CLI reads task files with the system encoding (cp1250 on a Romanian Windows machine) and would otherwise upload "BraČ™ov" instead of "Brașov".
- Erratum: task 13's description says "Brașov becomes Braºov". Precisely, the cedilla spelling Braşov becomes Braºov: Windows-1250 has no ș, so the task code converts to the cedilla first.
- The task code is left as it ran, so it matches this leaderboard. The known issues and the fixes for the next version are in the repository's [README](https://github.com/danielbutnar/comma-below#known-issues-in-the-pushed-tasks).
