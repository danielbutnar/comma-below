# results/

Every file here comes from a script in `analysis/`, run from the repo root. From a clone they rewrite these files
byte for byte, except `human_summary.json` (it needs the result codes people sent, which stay local) and
`post_table.md` (no script writes it now).

| File | What | Written by |
| --- | --- | --- |
| `raw/<task>/<version>/<model>/<run>/*.jsonl` | every scored answer, as Kaggle returned it. The run traces (`*.run.json`) stay on Kaggle. | `kaggle b t download` |
| `post_values.json` | every `{{NAME}}` number in the post | `analysis/check_claims.py --values` |
| `items.csv`, `summary.csv`, `summary.md`, `echo_runs.csv` | Round 1 (tasks 1-7, 1 October): per item, per model, task 2 per run | `analysis/analyze.py` |
| `post_stats.txt` | Round 1 numbers | `analysis/post_stats.py` |
| `post_table.md` | the results table of the post's first version (1 October) | none now |
| `items_round2.csv`, `round2_*.csv`, `round2_stats.txt` | Round 2 (tasks 8-12) | `analysis/round2.py` |
| `task13_stats.txt`, `task13_models.csv` | task 13 | `analysis/task13.py` |
| `human_summary.json` | totals of the human test | `analysis/human_summary.py` |

Without the run traces, `check_claims.py` keeps the values that need them (DeepSeek-R1's reasoning and the
cost) from the committed `post_values.json` and says so.
