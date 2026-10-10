"""Turn post/post-v3.md into post/post-v3-dev.md, the exact text pasted into DEV.

Numbers written as {{NAME}} come from results/post_values.json (written by analysis/check_claims.py),
so the post cannot drift from the data. Image placeholders become raw GitHub URLs; the cover has a new
file name because DEV caches images by URL. The checker embed comes from post/checker-tag.txt.

Usage:  uv run --no-project --with pandas --with numpy python analysis/check_claims.py --values
        uv run --no-project python post/finalize3.py [--draft]
"""

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RAW = "https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/"

s = (HERE / "post-v3.md").read_text(encoding="utf-8")
values = json.loads((HERE.parent / "results" / "post_values.json").read_text(encoding="utf-8"))
tag = HERE / "checker-tag.txt"
if tag.exists():
    values["CHECKER_TAG"] = tag.read_text(encoding="utf-8").strip()
for key, val in values.items():
    s = s.replace("{{" + key + "}}", str(val))
s = s.replace("COVER_URL", RAW + "cover-v2.png")
for name in ("HERO", "KEYBOARD", "WRONG", "UPGRADES", "FIXES"):
    s = s.replace(f"CHART_{name}_URL", RAW + f"chart-{name.lower()}.png")
if "--draft" in sys.argv:  # review copy: mark what is still missing instead of failing
    s = re.sub(r"\{\{([A-Z0-9_]+)\}\}", r"[pending: \1]", s)
left = re.findall(r"\{\{[A-Z0-9_]+\}\}|\b[A-Z0-9]+_URL\b", s)
assert not left, f"placeholders left: {sorted(set(left))}"
assert "**" not in re.sub(r"\*\*[^*\n]+\*\*", "", s), "unbalanced bold"
(HERE / "post-v3-dev.md").write_text(s, encoding="utf-8", newline="\n")
print("wrote post-v3-dev.md")
