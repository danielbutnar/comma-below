"""Write the model and task counts into post/cover.html (then render it with post/render.mjs).

Usage:  uv run --no-project python post/update_cover.py 44 12 [cover-v2.html]
"""

import pathlib
import re
import sys

n_models, n_tasks = int(sys.argv[1]), int(sys.argv[2])
p = pathlib.Path(__file__).resolve().parent / (sys.argv[3] if len(sys.argv) > 3 else "cover.html")
s = p.read_text(encoding="utf-8")
s = re.sub(r'<b id="models">\d+ models</b> · <b>\d+ tasks</b>',
           f'<b id="models">{n_models} models</b> · <b>{n_tasks} tasks</b>', s)
assert f"{n_models} models" in s and f"{n_tasks} tasks" in s
p.write_text(s, encoding="utf-8", newline="\n")
print("cover:", n_models, "models,", n_tasks, "tasks")
