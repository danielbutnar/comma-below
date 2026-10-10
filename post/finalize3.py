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
s = s.replace("COVER_URL", RAW + "cover-v3.png")
# DEV keeps its own copy of each image by URL, so a chart that changes after a paste gets a new file name
CHART_FILES = {"HERO": "chart-hero-v2.png", "KEYBOARD": "chart-keyboard-v2.png", "WRONG": "chart-wrong-v2.png",
               "UPGRADES": "chart-upgrades-v2.png", "FIXES": "chart-fixes-v5.png"}
for name, file in CHART_FILES.items():
    assert (HERE / file).exists(), f"missing {file}"
    s = s.replace(f"CHART_{name}_URL", RAW + file)
s = re.sub(r"(\d) %(?!\})", r"\1%", s)  # English typography on DEV: "96%", never a line break inside it
if "--draft" in sys.argv:  # review copy: mark what is still missing instead of failing
    s = re.sub(r"\{\{([A-Z0-9_]+)\}\}", r"[pending: \1]", s)
left = re.findall(r"\{\{[A-Z0-9_]+\}\}|\b[A-Z0-9]+_URL\b", s)
assert not left, f"placeholders left: {sorted(set(left))}"
assert "**" not in re.sub(r"\*\*[^*\n]+\*\*", "", s), "unbalanced bold"
(HERE / "post-v3-dev.md").write_text(s, encoding="utf-8", newline="\n")
print("wrote post-v3-dev.md")
