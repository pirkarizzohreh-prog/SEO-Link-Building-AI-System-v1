"""Free-tier fallback provider — not part of docs/ARCHITECTURE.md's
original OpenAI/Claude design. Added so the worker can run without paid
API billing set up: Groq's API is OpenAI-compatible (same request/response
shape), so this just points the official `openai` SDK at Groq's endpoint
instead of implementing a third HTTP client from scratch.

Groq's free tier has no listed per-token price, so `cost_estimate` is
always 0 here — it's a real gap (the `ai_jobs.cost_estimate` column stops
meaning "money spent" once Groq is the active provider), acceptable for a
dev/local fallback but worth knowing before reading that column.
"""

from __future__ import annotations

from openai import OpenAI

from app.core.config import settings
from app.models.ai_job import LlmProvider

from .base import BaseLLMClient, LLMResult

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# A current-generation, free-tier-friendly Groq-hosted model. Revisit if
# Groq retires it — check https://console.groq.com/docs/models.
MODEL = "llama-3.3-70b-versatile"


class GroqClient(BaseLLMClient):
    provider_name = LlmProvider.GROQ

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self._client = OpenAI(api_key=settings.GROQ_API_KEY, base_url=GROQ_BASE_URL)

    def generate(self, *, system_prompt: str, user_prompt: str, json_mode: bool = False) -> LLMResult:
        response = self._client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        return LLMResult(
            text=text,
            tokens_used=prompt_tokens + completion_tokens,
            cost_estimate=0.0,
            provider=self.provider_name,
        )
