from __future__ import annotations

from app.core.config import settings

from .base import BaseLLMClient


def get_default_provider() -> BaseLLMClient:
    """OpenAI primary, Claude fallback — see docs/ARCHITECTURE.md. Picked
    once per worker process run, not per job, so a single run is
    consistent about which provider it used (and `ai_jobs.provider`
    reflects that truthfully).

    Groq is a third, free-tier fallback — not part of the original
    design, added for local/dev use without paid API billing (see
    app/ai/providers/groq_provider.py).
    """
    if settings.OPENAI_API_KEY:
        from .openai_provider import OpenAIClient

        return OpenAIClient()
    if settings.ANTHROPIC_API_KEY:
        from .claude_provider import ClaudeClient

        return ClaudeClient()
    if settings.GROQ_API_KEY:
        from .groq_provider import GroqClient

        return GroqClient()
    raise RuntimeError(
        "No LLM provider configured — set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROQ_API_KEY before running the worker."
    )
