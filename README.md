# Comma Below

A Kaggle benchmark on one Romanian letter pair: **ș ț** (s and t with a comma below, U+0219 / U+021B, the
correct Romanian letters) versus **ş ţ** (s and t with a cedilla, U+015F / U+0163), a legacy encoding
workaround that still fills the Romanian web. The two look almost identical and are different characters.

Thirteen tasks, every score computed from Unicode code points (after NFC). No LLM judge.

- **Benchmark and leaderboard:** https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below
- **Write-up:** https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a

| # | Task | Question | Items |
| --- | --- | --- | --- |
| 1 | Write | From English prompts (ASCII place names), does the model write ș/ț correctly? | 24 |
| 2 | Echo | When the user's text is typed with cedilla, does the reply, summary or retrieval answer copy it? Paired with a clean control. | 44 |
| 3 | Fix | Asked to proofread cedilla text (plain → explicit instruction), does it repair the letters? | 18 |
| 4 | See | Can it tell ş from ș? Same/different, detection, code point. | 36 |
| 5 | Restore | Put diacritics back into ASCII Romanian where context decides (peste/pește). | 30 |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests. | 2 |
| 7 | Echo with a rule | Echo's cedilla inputs again, with one system-prompt sentence asking for comma-below letters. | 22 |
| 8 | Echo, four inputs | Echo's 22 prompts typed clean, with cedilla, without diacritics, and with cedilla + the rule; every model Kaggle serves. | 88 |
| 9 | Contagion | Four documents and a question about one; 0, 1 or 3 of the others typed with cedilla, or the target. | 40 |
| 10 | Turkish guests | Turkish (where ş is correct) under no rule, task 7's rule, and the same rule scoped to Romanian. | 36 |
| 11 | Other look-alikes | English text typed with Cyrillic look-alike letters (in every word, or only in the names) or as mojibake (ZÃ¼rich). | 48 |
| 12 | Turns | Two summaries in one chat: does a cedilla first text infect the second? | 18 |
| 13 | Other wrong letters | Task 8's summaries and document questions typed with a dot below (Braṣov) or old Windows-1250 mojibake (Braºov) instead of the cedilla, and with the scoped and the full rule. | 80 |

Tasks 8–13 (Round 2) carry predictions in their Kaggle descriptions, pushed before any model ran them.

Also here:

- **A two-minute human test** on task 4's word pairs: https://danielbutnar.github.io/comma-below/human/test.html (`human/test.html`; Romanian, German, English; nothing is sent or stored). Only totals are published (`results/human_summary.json`). Version 1 (until 10 Oct) marked the words as Romanian, and on a Romanian page fonts such as Segoe UI, Roboto, Noto Sans and Open Sans draw ş with a comma, so many people saw two identical words; version 2 marks them as English and scores identical and different pairs separately. The two versions are summarised apart.
- **A cedilla checker** for any text (`post/checker.html`), embedded in the write-up. Its fix is the post's `fix_romanian()`: it swaps ş ţ for ș ț sentence by sentence; in a sentence with ı ğ ç ö ü it swaps only ţ (Turkish has no ţ) and leaves ş alone. A Turkish sentence without those letters ("Hoş geldiniz!") still gets changed, and a Romanian sentence quoting Zürich keeps its ş (the checker says so). `analysis/fix_check.py` measures it on the models' Turkish and Romanian answers.

## Layout

- `src/items.py`: all items. Romanian is written in correct orthography; cedilla, ASCII, Cyrillic and mojibake
  variants are generated, never typed.
- `src/scoring.py`: scoring helpers, pasted into every task.
- `src/build.py`: renders `tasks/*.py`. The task files are ASCII-only (`\u` escapes) and check a SHA-256 of their data
  before running, because the Kaggle CLI reads task files with the locale encoding (cp1250 here) and would push
  "BraČ™ov" instead of "Brașov".
- `src/dry_run.py`: runs the tasks locally against ten fake models (perfect, cedilla, stripped, mirroring, sticky,
  normalizing, a mojibake reader, flaky, picky, thinking) and asserts the expected scores. `python src/dry_run.py -8- -9-`
  runs a subset.
- `analysis/`: web census of cedilla use on Romanian front pages; `analyze.py` loads the runs; `post_stats.py` (Round 1)
  and `round2.py` (Round 2, with bootstrap intervals, McNemar tests and version trends); `task13.py` (the analysis
  pre-registered in task 13); `own_words.py` (do the model's own words follow a copied cedilla?); `fix_check.py`;
  `human_summary.py`; `models.py` (labs, product lines, versions); `charts.py`, `charts2.py`, `charts3.py`;
  `check_claims.py` recomputes the numbers the post quotes and scores the predictions; cost and quota scripts.
- `results/`: every scored answer as Kaggle returned it (`results/raw/<task>/<version>/<model>/<run>/*.jsonl`, the rows the analysis reads; the run traces stay on Kaggle), per-item tables (`items.csv`, `items_round2.csv`), per-model summaries, Round 2 tables, Echo runs.
- `post/`: cover, charts and the text of the write-up.

## Run

```bash
uv run --no-project --with pandas python src/build.py
uv run --no-project --with pandas --with-editable <path-to>/kaggle-benchmarks python src/dry_run.py
PYTHONUTF8=1 kaggle b t push romanian-comma-below-1-write -f tasks/romanian-comma-below-1-write.py --wait
PYTHONUTF8=1 kaggle b t run romanian-comma-below-1-write -m gemini-3.8-flash
PYTHONUTF8=1 kaggle b t download romanian-comma-below-8-echo-four-inputs -o results/raw   # optional: the answers are committed
uv run --no-project --with pandas --with numpy python analysis/round2.py
uv run --no-project --with pandas --with numpy python analysis/check_claims.py
```

License: MIT.

Answer keys were checked by a native Romanian speaker. The Turkish and English texts of tasks 10 and 11 were not
checked by native speakers; only the letters under test are scored.
