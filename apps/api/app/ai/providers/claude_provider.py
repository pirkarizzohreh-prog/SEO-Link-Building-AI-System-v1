from __future__ import annotations

from anthropic import Anthropic

from app.core.config import settings
from app.models.ai_job import LlmProvider

from .base import BaseLLMClient, LLMResult

MODEL = "claude-3-5-haiku-20241022"
_INPUT_COST_PER_1K = 0.0008
_OUTPUT_COST_PER_1K = 0.004

_JSON_ONLY_SUFFIX = (
    "\n\nRespond with ONLY a single valid JSON object or array — no markdown code "
    "fences, no commentary before or after it."
)


class ClaudeClient(BaseLLMClient):
    """Fallback/secondary provider — see docs/ARCHITECTURE.md. Anthropic's
    Messages API has no strict "JSON mode" like OpenAI's, so `json_mode`
    is enforced by instruction only; callers must still parse
    defensively (app/ai/json_utils.py strips stray code fences).
    """

    provider_name = LlmProvider.CLAUDE

    def __init__(self) -> None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(self, *, system_prompt: str, user_prompt: str, json_mode: bool = False) -> LLMResult:
        if json_mode:
            system_prompt = system_prompt + _JSON_ONLY_SUFFIX

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1000) * _INPUT_COST_PER_1K + (output_tokens / 1000) * _OUTPUT_COST_PER_1K
        return LLMResult(
            text=text,
            tokens_used=input_tokens + output_tokens,
            cost_estimate=round(cost, 6),
            provider=self.provider_name,
        )
