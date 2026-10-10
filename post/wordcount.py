"""Count the words a DEV reader sees without opening anything, and fail above the budget.

Visible = outside {% details %} blocks, code blocks and liquid tags; image links and bare URLs don't
count, link text does. Table cells count. Usage:
  uv run --no-project python post/wordcount.py post/post-v2-dev.md [--max 2300]
"""

from __future__ import annotations

import re
import sys


def visible_text(md: str) -> tuple[str, str]:
    """(visible markdown, collapsed markdown)."""
    collapsed = []

    def hide(m):
        collapsed.append(m.group(0))
        return ""

    md = re.sub(r"\{%\s*details.*?%\}.*?\{%\s*enddetails\s*%\}", hide, md, flags=re.S)
    md = re.sub(r"^---\n.*?\n---\n", "", md, count=1, flags=re.S)       # front matter
    md = re.sub(r"```.*?```", " ", md, flags=re.S)                       # code blocks
    md = re.sub(r"\{%.*?%\}", " ", md, flags=re.S)                       # other liquid tags
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)                        # images
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)                     # links keep their text
    md = re.sub(r"https?://\S+", " ", md)                                # bare URLs
    md = re.sub(r"<[^>]+>", " ", md)                                     # html tags
    return md, "\n".join(collapsed)


def count(text: str) -> int:
    return len(re.findall(r"[^\W_]+(?:[-'’.,][^\W_]+)*", text))


def main():
    path = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 2300
    md = open(path, encoding="utf-8").read()
    vis, hidden = visible_text(md)
    n, h = count(vis), count(hidden)
    print(f"{path}: {n} visible words (limit {limit}), {h} more inside details blocks")
    if n > limit:
        sys.exit(f"over budget by {n - limit} words")


if __name__ == "__main__":
    main()
