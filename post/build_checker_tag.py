"""Turn post/checker.html into the DEV liquid tag that embeds it (post/checker-tag.txt).

LiveCodes renders a page carried entirely in its URL, so nothing is uploaded and no account is needed.
No network access here: the page is only escaped to ASCII and percent-encoded. finalize3.py inserts the tag.
The script's comment lines stay in checker.html and are left out of the embed, and spaces are written as "+"
(as URLSearchParams writes them): that keeps the URL under 16,000 characters, since servers and CDNs refuse
request URLs much longer than that.
GitHub Pages also serves the page on its own (STANDALONE below), for readers whose feed or reader drops the embed.
Usage:  uv run --no-project python post/build_checker_tag.py
"""

import pathlib
import re
from urllib.parse import quote_plus

HERE = pathlib.Path(__file__).resolve().parent
BACKSLASH = chr(92)
# Tall enough that on a 360 px phone the Fix button shows after "Show Claude Opus 5.5's real answer"
# (its bottom is at 659 px in headless Chromium, 680 px at 336 px wide), with room for LiveCodes' drawer.
HEIGHT = 760
STANDALONE = "https://danielbutnar.github.io/comma-below/post/checker.html"
FALLBACK = f"(No box above? [Open the checker on its own page]({STANDALONE}).)"

page = (HERE / "checker.html").read_text(encoding="utf-8")


def without_comment_lines(html: str) -> str:
    """The script without its // comment lines (they stay in checker.html)."""
    return re.sub(r"<script>.*?</script>", lambda m: re.sub(r"\n[ \t]*//[^\n]*", "", m.group(0)), html, flags=re.S)


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


html = re.sub(r"\n\s+", "\n", ascii_only(without_comment_lines(page)))
assert html.isascii() and "//" not in re.sub(r"https?://", "", html), "a comment survived"
url = "https://livecodes.io/?mode=result&title=Cedilla%20checker&html=" + quote_plus(html, safe="")
assert len(url) < 16000, f"the embed URL is {len(url)} characters; shorten checker.html"
# the pattern DEV's livecodes tag accepts (forem app/liquid_tags/livecodes_tag.rb)
assert re.fullmatch(r"https://(?:[a-zA-Z0-9-]{1,20}\.)?livecodes\.io(?:/?|/?\?[^\s#]*|/?\#\S*)", url)
(HERE / "checker-tag.txt").write_text("{% livecodes " + url + f" height={HEIGHT} %}}\n", encoding="utf-8", newline="\n")
print(f"wrote checker-tag.txt: {len(url)} characters, height {HEIGHT}")
print("fallback line for the post:", FALLBACK)
