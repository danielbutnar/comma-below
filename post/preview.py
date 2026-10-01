"""Render post/post.md to post/preview.html for review (images inlined).

Usage:  uv run --no-project --with markdown python post/preview.py
"""

import base64
import pathlib
import re

import markdown

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / "post.md").read_text(encoding="utf-8")
front, body = re.match(r"^---\n(.*?)\n---\n(.*)$", src, re.S).groups()
title = re.search(r"^title:\s*(.+)$", front, re.M).group(1)


def data_uri(name):
    return "data:image/png;base64," + base64.b64encode((HERE / name).read_bytes()).decode()


images = {"CHART_CENSUS_URL": "chart-web-census.png", "CHART_ECHO_URL": "chart-echo.png",
          "CHART_SEE_URL": "chart-see.png"}
for key, file in images.items():
    body = body.replace(key, data_uri(file))
for key in ("TASK7_RESULT", "GITHUB_LINE"):
    body = body.replace(key, f'<mark class="todo">[{key}: still to fill in]</mark>')

html_body = markdown.markdown(body, extensions=["tables", "fenced_code"])

page = f"""<title>Comma Below draft</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600;7..72,700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* Layout: one reading column like the DEV article view, cover on top, review banner above it */
:root {{
  --bg: #fbfbfa; --fg: #1d1f22; --muted: #5f646b; --rule: #e3e4e6; --code-bg: #f1f2f4;
  --accent: #2a78d6; --flag-bg: #fff3c4; --flag-fg: #5b4500;
  --serif: "Literata", Georgia, "Times New Roman", serif;
  --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #17181a; --fg: #e9e9e7; --muted: #a3a6ab; --rule: #2e3034; --code-bg: #222428;
  --accent: #6da7ec; --flag-bg: #4a3b00; --flag-fg: #ffe9a3; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #17181a; --fg: #e9e9e7; --muted: #a3a6ab; --rule: #2e3034; --code-bg: #222428;
  --accent: #6da7ec; --flag-bg: #4a3b00; --flag-fg: #ffe9a3; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font: 18px/1.65 var(--serif); padding-inline: 16px; padding-block: 24px 64px; }}
.wrap {{ max-width: 720px; margin: 0 auto; display: grid; gap: 4px; }}
.banner {{ font: 500 13px/1.4 var(--mono); color: var(--flag-fg); background: var(--flag-bg); padding: 10px 14px; border-radius: 6px; }}
.cover {{ width: 100%; border-radius: 8px; margin-block: 12px 8px; }}
h1 {{ font-size: clamp(28px, 5vw, 40px); line-height: 1.15; text-wrap: balance; margin: 12px 0 4px; }}
.tags {{ font: 14px var(--mono); color: var(--muted); margin-bottom: 16px; }}
h2 {{ font-size: 28px; line-height: 1.25; margin: 40px 0 8px; text-wrap: balance; }}
h3 {{ font-size: 21px; line-height: 1.3; margin: 28px 0 4px; text-wrap: balance; }}
p, li {{ max-width: 68ch; }}
a {{ color: var(--accent); }}
blockquote {{ margin: 16px 0; padding: 4px 0 4px 18px; border-left: 3px solid var(--rule); color: var(--fg); font-size: 19px; }}
img {{ max-width: 100%; height: auto; }}
p > img {{ display: block; margin: 16px 0; border: 1px solid var(--rule); border-radius: 6px; background: #fcfcfb; }}
code {{ font: 0.86em var(--mono); background: var(--code-bg); padding: 1px 5px; border-radius: 4px; }}
pre {{ background: var(--code-bg); padding: 14px 16px; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; font-size: 15px; line-height: 1.5; }}
.table {{ overflow-x: auto; margin: 12px 0; }}
table {{ border-collapse: collapse; font-size: 16px; min-width: 100%; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font-weight: 600; }}
mark.todo {{ background: var(--flag-bg); color: var(--flag-fg); padding: 0 4px; border-radius: 3px; font: 500 0.85em var(--mono); }}
</style>
<div class="wrap">
  <div class="banner">Draft for review · not published · cover, charts and numbers are final candidates</div>
  <img class="cover" src="{data_uri('cover.png')}" alt="Braşov ≠ Brașov: U+015F s with cedilla versus U+0219 s with comma below">
  <h1>{title}</h1>
  <div class="tags">#devchallenge #kagglechallenge #ai #machinelearning</div>
  {html_body.replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")}
</div>
"""
(HERE / "preview.html").write_text(page, encoding="utf-8", newline="\n")
print("wrote preview.html", len(page) // 1024, "KB")
