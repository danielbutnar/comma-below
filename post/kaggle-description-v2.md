Romanian writes **ș** and **ț** with a comma below (U+0219, U+021B). In the 1990s the common encodings had no such letters, so Romanian text used the look-alike **ş** and **ţ** with a cedilla (U+015F, U+0163). On 30 September 2026, 29 of 35 Romanian front pages I checked (government, National Bank, Brașov city hall, rail operator, news sites) still had cedilla letters in Romanian words.

The two look almost identical and are different characters: `==`, `grep`, SQL with a binary collation, site search, deduplication and URL slugs treat them as two words.

**Write-up:** https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

**Code, raw answers, analysis and a claim checker:** https://github.com/danielbutnar/comma-below

Every score is computed from Unicode code points after NFC normalization; there is no LLM judge. Answer keys were checked by a native Romanian speaker. Every task was first run against nine fake models with known behaviour and their scores asserted.

| # | Task | What it measures |
| --- | --- | --- |
| 1 | Write | From English prompts with ASCII place names, does the model write ș/ț? |
| 2 | Echo | The same guest messages and news paragraphs, typed correctly and typed with cedilla. Does the reply, summary or document answer copy the wrong letters? Score = cedilla inputs. |
| 3 | Fix | Cedilla text plus one typo, under "proofread", "correct the spelling and the diacritics", and an explicit instruction. |
| 4 | See | Same/different pairs (half byte-identical), cedilla detection in a sentence, code point at a position. |
| 5 | Restore | Put diacritics back where only context decides (peste/pește, fata/fața). |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests (uppercase, decomposed s + U+0327, French ç). |
| 7 | Echo + rule | Echo's cedilla inputs with one system-prompt sentence asking for comma-below letters. |
| 8 | Echo, four inputs | Echo's 22 prompts typed correctly, with cedilla, without diacritics, and with cedilla + the rule; every model Kaggle serves. Score = cedilla inputs. |
| 9 | Contagion | Four documents, a question about one; 0, 1 or 3 of the others typed with cedilla, or the target itself. |
| 10 | Turkish guests | Turkish (ş is correct there) under no rule, task 7's rule, and the same rule scoped to Romanian. |
| 11 | Other look-alikes | English text typed with Cyrillic look-alike letters (а с е о р) or as mojibake (ZÃ¼rich). |
| 12 | Turns | Two summaries in one chat: does a cedilla first text change the second? |
| 13 | Other wrong letters | Task 8's summaries and document questions typed with a dot below (Braṣov) or as old Windows-1250 mojibake (Braºov) instead of the cedilla, and with the scoped and the full rule. |

Tasks 8–13 carry predictions in their descriptions, written and pushed before any model ran them.

**Reading the leaderboard.** Several tasks are controls where every model is near 100 % (Write, See, Fix), and the follow-up tasks 9–13 ran on fewer models, so read the overall score as a rough summary. Task 8's own leaderboard ranks the models on the copying itself: the share of clean answers when the input has cedillas.

**Notes on method**

- Output is capped at 8,192 tokens per call. Answers are scored on their visible text; inline `<think>` reasoning is removed first.
- Models reached through the OpenAI-compatible proxy run at the provider's default temperature. The post reports Echo as the mean of four runs for the 15 core models (tasks 2 and 8); the leaderboard shows each model's latest run.
- Grok 4.5 and Grok 4.6 are listed by Kaggle but returned errors; gpt-oss-120b's provider was overloaded during the first round.
- Task source files are ASCII-only and verify a SHA-256 of their data before running, because the Kaggle CLI reads task files with the system encoding (cp1250 on a Romanian Windows machine) and would otherwise upload "BraČ™ov" instead of "Brașov".
