"""Turn post/checker.html into the DEV liquid tag that embeds it (post/checker-tag.txt).

LiveCodes renders a page carried entirely in its URL, so nothing is uploaded and no account is needed.
No network access here: the page is only escaped to ASCII and percent-encoded. finalize3.py inserts the tag.
Usage:  uv run --no-project python post/build_checker_tag.py
"""

import pathlib
import re
from urllib.parse import quote

HERE = pathlib.Path(__file__).resolve().parent
BACKSLASH = chr(92)

page = (HERE / "checker.html").read_text(encoding="utf-8")


def ascii_only(html: str) -> str:
    """Non-ASCII as \\uXXXX inside <script>, as &#x...; elsewhere."""
    parts = re.split(r"(<script>.*?</script>)", html, flags=re.S)
    out = []
    for part in parts:
        if part.startswith("<script>"):
            out.append("".join(c if ord(c) < 128 else BACKSLASH + "u%04X" % ord(c) for c in part))
        else:
            out.append("".join(c if ord(c) < 128 else "&#x%X;" % ord(c) for c in part))
    return "".join(out)


html = re.sub(r"\n\s+", "\n", ascii_only(page))
assert html.isascii()
url = "https://livecodes.io/?mode=result&title=Cedilla%20checker&html=" + quote(html, safe="")
# the pattern DEV's livecodes tag accepts (forem app/liquid_tags/livecodes_tag.rb)
assert re.fullmatch(r"https://(?:[a-zA-Z0-9-]{1,20}\.)?livecodes\.io(?:/?|/?\?[^\s#]*|/?\#\S*)", url)
(HERE / "checker-tag.txt").write_text("{% livecodes " + url + " height=720 %}\n", encoding="utf-8", newline="\n")
print(f"wrote checker-tag.txt: {len(url)} characters")
