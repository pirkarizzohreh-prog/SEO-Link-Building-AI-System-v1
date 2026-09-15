from __future__ import annotations

from app.core.config import settings

from .base import BaseLLMClient


def get_default_provider() -> BaseLLMClient:
    """OpenAI primary, Claude fallback — see docs/ARCHITECTURE.md. Picked
    once per worker process run, not per job, so a single run is
    consistent about which provider it used (and `ai_jobs.provider`
    reflects that truthfully).
    """
    if settings.OPENAI_API_KEY:
        from .openai_provider import OpenAIClient

        return OpenAIClient()
    if settings.ANTHROPIC_API_KEY:
        from .claude_provider import ClaudeClient

        return ClaudeClient()
    raise RuntimeError(
        "No LLM provider configured — set OPENAI_API_KEY or ANTHROPIC_API_KEY before running the worker."
    )
