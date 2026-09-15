from __future__ import annotations

from openai import OpenAI

from app.core.config import settings
from app.models.ai_job import LlmProvider

from .base import BaseLLMClient, LLMResult

# Chosen for cost/latency on the short-to-medium prompts this MVP sends
# (keyword/topic/brief generation, article drafts); revisit once real
# usage data exists. Rough per-1K-token USD pricing below is for the
# `cost_estimate` column's visibility into spend, not billing-accurate.
MODEL = "gpt-4o-mini"
_INPUT_COST_PER_1K = 0.00015
_OUTPUT_COST_PER_1K = 0.0006


class OpenAIClient(BaseLLMClient):
    provider_name = LlmProvider.OPENAI

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

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
        cost = (prompt_tokens / 1000) * _INPUT_COST_PER_1K + (completion_tokens / 1000) * _OUTPUT_COST_PER_1K
        return LLMResult(
            text=text,
            tokens_used=prompt_tokens + completion_tokens,
            cost_estimate=round(cost, 6),
            provider=self.provider_name,
        )
