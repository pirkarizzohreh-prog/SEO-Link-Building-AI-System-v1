"""A canned-response BaseLLMClient for tests — no network, no cost, no
API keys needed. Agents are written against BaseLLMClient (never a
concrete SDK), so this is a drop-in for app/jobs/handlers.process_job in
tests.
"""

from __future__ import annotations

from app.ai.providers.base import BaseLLMClient, LLMResult
from app.models.ai_job import LlmProvider


class FakeLLMClient(BaseLLMClient):
    provider_name = LlmProvider.OPENAI

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def generate(self, *, system_prompt: str, user_prompt: str, json_mode: bool = False) -> LLMResult:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt, "json_mode": json_mode})
        if not self._responses:
            raise AssertionError("FakeLLMClient ran out of canned responses")
        text = self._responses.pop(0)
        return LLMResult(text=text, tokens_used=100, cost_estimate=0.001, provider=self.provider_name)
