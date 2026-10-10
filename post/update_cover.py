"""Write the model and task counts into a cover (then render it with post/render.mjs).

The model count is the four-way test's (N_MODELS in results/post_values.json), the one in the post's
title; the task count is every task in the benchmark.

Usage:  uv run --no-project python post/update_cover.py 43 13 [cover-v3.html]
"""

import pathlib
import re
import sys

n_models, n_tasks = int(sys.argv[1]), int(sys.argv[2])
p = pathlib.Path(__file__).resolve().parent / (sys.argv[3] if len(sys.argv) > 3 else "cover-v3.html")
s = p.read_text(encoding="utf-8")
s = re.sub(r'<b id="models">\d+ models</b>', f'<b id="models">{n_models} models</b>', s)
s = re.sub(r'(<b id="tasks">|<b>)\d+ tasks</b>', rf'\g<1>{n_tasks} tasks</b>', s)
assert f"{n_models} models</b>" in s and f"{n_tasks} tasks</b>" in s
p.write_text(s, encoding="utf-8", newline="\n")
print("cover:", n_models, "models,", n_tasks, "tasks")
