"""Just enough Markdown -> HTML to hand an article's body to a blog CMS's
"Text"/HTML editor mode — not a general Markdown renderer. Article content
only ever comes from the Article Writer prompt (app/ai/prompts/
article_writer.md: "خروجی را به‌صورت Markdown با H2/H3 مشخص بازگردان"), a
known, narrow subset: H2/H3 headings, `[text](url)` links, and paragraphs.
Stdlib-only, same "good enough for this one caller" spirit as
app/ai/html_extract.py.
"""

from __future__ import annotations

import re
from html import escape

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text: str) -> str:
    """Escapes everything except `[label](url)` spans, which become real
    `<a>` tags — escaping the whole line first and then substituting links
    into it would double-escape the label/url, so the two have to happen
    in one pass.
    """
    pieces: list[str] = []
    last_end = 0
    for match in _LINK_RE.finditer(text):
        pieces.append(escape(text[last_end : match.start()]))
        label, url = match.groups()
        pieces.append(f'<a href="{escape(url, quote=True)}">{escape(label)}</a>')
        last_end = match.end()
    pieces.append(escape(text[last_end:]))
    return "".join(pieces)


def markdown_to_html(markdown_text: str) -> str:
    html_parts: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            html_parts.append(f"<p>{' '.join(_inline(line) for line in paragraph_lines)}</p>")
            paragraph_lines.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 6)
            html_parts.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        paragraph_lines.append(line)

    flush_paragraph()
    return "\n".join(html_parts)
