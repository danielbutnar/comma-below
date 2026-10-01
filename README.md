# Comma Below

A Kaggle benchmark on one Romanian letter pair: **ș ț** (s and t with a comma below, U+0219 / U+021B, the
correct Romanian letters) versus **ş ţ** (s and t with a cedilla, U+015F / U+0163), a legacy encoding
workaround that still fills the Romanian web. The two look almost identical and are different characters.

Seven tasks, every score computed from Unicode code points (after NFC). No LLM judge.

- **Benchmark and leaderboard:** https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below
- **Write-up:** DEV_POST_URL

| # | Task | Question | Items |
| --- | --- | --- | --- |
| 1 | Write | From English prompts (ASCII place names), does the model write ș/ț correctly? | 24 |
| 2 | Echo | When the user's text is typed with cedilla, does the reply, summary or retrieval answer copy it? Paired with a clean control. | 44 |
| 3 | Fix | Asked to proofread cedilla text (plain → explicit instruction), does it repair the letters? | 18 |
| 4 | See | Can it tell ş from ș? Same/different, detection, code point. | 36 |
| 5 | Restore | Put diacritics back into ASCII Romanian where context decides (peste/pește). | 30 |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests. | 2 |
| 7 | Echo with a rule | Echo's cedilla inputs again, with one system-prompt sentence asking for comma-below letters. | 22 |

## Layout

- `src/items.py`: all items in correct Romanian. Cedilla and diacritic-free variants are generated, never typed.
- `src/scoring.py`: scoring helpers, pasted into every task.
- `src/build.py`: renders `tasks/*.py`. The task files are ASCII-only (`\u` escapes) and check a SHA-256 of their data
  before running, because the Kaggle CLI reads task files with the locale encoding (cp1250 here) and would push
  "BraČ™ov" instead of "Brașov".
- `src/dry_run.py`: runs every task locally against fake models (perfect, cedilla, stripped, mirroring, flaky,
  picky, thinking) and asserts the expected scores.
- `analysis/`: web census of cedilla use on Romanian front pages, cost and quota scripts, result tables, charts.
- `results/`: per-item answers and scores for every model (`items.csv`), per-model summary, Echo runs.
- `post/`: cover, charts and the text of the write-up.

## Run

```bash
uv run --no-project --with pandas python src/build.py
uv run --no-project --with pandas --with-editable <path-to>/kaggle-benchmarks python src/dry_run.py
PYTHONUTF8=1 kaggle b t push romanian-comma-below-1-write -f tasks/romanian-comma-below-1-write.py --wait
PYTHONUTF8=1 kaggle b t run romanian-comma-below-1-write -m gemini-3.8-flash
```

License: MIT.

Answer keys were checked by a native Romanian speaker.
