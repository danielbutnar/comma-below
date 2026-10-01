Romanian writes **ș** and **ț** with a comma below (U+0219, U+021B). In the 1990s the common encodings (ISO 8859-2, Windows-1250) had no such letters, so Romanian text used the look-alike **ş** and **ţ** with a cedilla (U+015F, U+0163). Unicode added the correct letters in 1999, but the old ones never left: on 30 September 2026, 30 of 35 Romanian front pages I checked (government, national bank, Brașov city hall, rail operator, news sites) still contained cedilla letters.

The two look almost identical, and they are different characters. Search, sorting, deduplication, spell-checkers and screen readers treat them differently.

This benchmark asks six questions. Every score is computed from Unicode code points after NFC normalization; there is no LLM judge. The answer keys were checked by a native Romanian speaker.

| # | Task | What it measures |
| --- | --- | --- |
| 1 | Write | From English prompts with ASCII place names (Timisoara, Brasov), does the model write the correct letters? |
| 2 | Echo | The same guest messages and news paragraphs arrive clean and typed with cedilla. Does the reply, summary or retrieval-style answer copy the wrong letters? Score = pass rate on the cedilla inputs; on clean inputs every model scores 100 %. |
| 3 | Fix | Cedilla text plus one ordinary typo, under three instructions: plain "proofread", "correct the spelling and the diacritics", and an explicit description of the problem. |
| 4 | See | Can the model tell the letters apart? Same/different pairs (half are byte-identical), detection in a sentence, and the code point at a position. |
| 5 | Restore | Put the diacritics back into Romanian typed without them, where only context decides (peste/pește, fata/fața, masa/masă). |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests cover uppercase, decomposed forms (s + U+0327), text that is already correct, and French ç that must not change. |

**Notes on method**

- Task source files are ASCII-only and verify a SHA-256 of their data before running, because the Kaggle CLI reads task files with the system encoding (cp1250 on a Romanian Windows machine) and would otherwise upload "BraČ™ov" instead of "Brașov".
- Output is capped at 8,192 tokens per call. Answers are scored on their visible text; inline `<think>` reasoning is removed first.
- Models reached through the OpenAI-compatible proxy run at the provider's default temperature, so Echo was run several times per model.
- gpt-oss-120b's provider was overloaded during the runs; some of its items are missing.

Write-up: (DEV post link)
