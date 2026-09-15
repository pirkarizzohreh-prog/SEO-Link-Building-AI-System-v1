"""Deterministic (non-LLM) HTML signal extraction for Competitor
Intelligence — docs/AI_WORKFLOW.md: "fetch محتوای صفحه رقیب (HTTP ساده در
MVP؛ بدون رندر جاوااسکریپت سنگین) → استخراج heading structure و
کلیدواژه‌های پرتکرار". Stdlib-only (html.parser) — deliberately not a
full readability/boilerplate-stripping pass; good enough to feed the LLM
comparison step, not meant to be a general-purpose scraper.
"""

from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "this", "that", "it", "as", "by", "be", "at", "from",
    "your", "you", "we", "our", "can", "will", "how", "what", "why", "not",
}

_HEADING_TAGS = {"h1", "h2", "h3"}
_SKIP_TAGS = {"script", "style", "noscript"}
_WORD_RE = re.compile(r"[a-zA-Z؀-ۿ]{3,}")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self._current_tag: str | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        self._current_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        self._current_tag = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        if self._current_tag == "title":
            self.title = text
        elif self._current_tag in _HEADING_TAGS:
            self.headings.append(text)
        self.text_parts.append(text)


def extract_page_signals(html: str, *, top_keywords_count: int = 15) -> dict:
    parser = _PageParser()
    parser.feed(html)

    full_text = " ".join(parser.text_parts)
    words = [w.lower() for w in _WORD_RE.findall(full_text)]
    word_count = len(words)
    keyword_counts = Counter(w for w in words if w not in _STOPWORDS)
    top_keywords = [word for word, _ in keyword_counts.most_common(top_keywords_count)]

    return {
        "title": parser.title,
        "headings": parser.headings,
        "word_count": word_count,
        "top_keywords": top_keywords,
    }
