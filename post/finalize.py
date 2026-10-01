"""Turn post/post.md into post/post-dev.md, the exact text pasted into DEV.

Usage:  uv run --no-project python post/finalize.py
"""

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
RAW = "https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/"
REPO = "https://github.com/danielbutnar/comma-below"

s = (HERE / "post.md").read_text(encoding="utf-8")
s = s.replace("COVER_URL", RAW + "cover.png")
s = s.replace("CHART_CENSUS_URL", RAW + "chart-web-census.png")
s = s.replace("CHART_ECHO_URL", RAW + "chart-echo.png")
s = s.replace("CHART_SEE_URL", RAW + "chart-see.png")
s = s.replace("GITHUB_LINE", f"on GitHub: [github.com/danielbutnar/comma-below]({REPO}).")
left = re.findall(r"\b[A-Z0-9]+_(?:URL|RESULT|LINE)\b", s)
assert not left, f"placeholders left: {left}"
(HERE / "post-dev.md").write_text(s, encoding="utf-8", newline="\n")
print("wrote post-dev.md,", len(s.split()), "words")
