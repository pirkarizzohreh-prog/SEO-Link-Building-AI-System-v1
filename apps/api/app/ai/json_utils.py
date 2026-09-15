"""Defensive JSON parsing for LLM output.

Even in "JSON mode", models occasionally wrap output in markdown code
fences or add stray whitespace. This strips the common cases before
handing off to `json.loads`, so agents don't each reimplement it — but a
genuinely malformed response still raises, surfacing as a failed
`ai_jobs` row rather than silently producing garbage rows.
"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMOutputParseError(ValueError):
    pass


def parse_json_response(text: str) -> dict | list:
    cleaned = _FENCE_RE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMOutputParseError(f"Model did not return valid JSON: {exc}. Raw text: {text[:500]!r}") from exc
