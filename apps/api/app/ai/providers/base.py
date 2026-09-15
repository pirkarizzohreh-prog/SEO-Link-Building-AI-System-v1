"""LLM provider abstraction — see docs/ARCHITECTURE.md ("AI Layer") and
docs/AI_WORKFLOW.md's prompt design principles.

Every agent calls `BaseLLMClient.generate(...)` through this one
interface, never the OpenAI/Anthropic SDKs directly — swapping or A/B
testing providers is then a config change, not a code change, and every
call's token/cost usage is reported in one shape regardless of which
provider actually served it (logged onto `ai_jobs` by app/jobs/handlers.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.ai_job import LlmProvider


@dataclass
class LLMResult:
    text: str
    tokens_used: int
    cost_estimate: float
    provider: LlmProvider


class BaseLLMClient(ABC):
    provider_name: LlmProvider

    @abstractmethod
    def generate(self, *, system_prompt: str, user_prompt: str, json_mode: bool = False) -> LLMResult:
        """Run one completion. When `json_mode` is True, the provider is
        instructed to return a single JSON object/array and callers should
        still validate/parse defensively — no provider's "JSON mode" is a
        hard schema guarantee.
        """
        raise NotImplementedError
