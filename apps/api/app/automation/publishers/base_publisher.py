"""Publisher interface — docs/PROJECT_STRUCTURE.md's `base_publisher.py` /
`<platform>_publisher.py` split: one Playwright script per blog platform
behind one shared interface, so `app/ai/agents/publish_agent.py` never
branches on which CMS it's talking to.

Mirrors `app/ai/providers/base.py`'s `BaseLLMClient` shape deliberately —
same reason: agents/callers depend on the ABC, tests inject a fake
(`tests/fake_publisher.py`), never a real browser.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PublishPayload:
    title: str
    content_html: str
    login_url: str
    username: str
    password: str
    category: str | None = None


@dataclass
class PublishResult:
    success: bool
    published_url: str | None = None
    error_message: str | None = None


class BasePublisher(ABC):
    @abstractmethod
    def publish(self, payload: PublishPayload) -> PublishResult:
        """Logs in, creates a post, publishes it, and returns its live URL.

        Must never raise for an ordinary automation failure (wrong
        selector, login rejected, network error) — catch it and return
        `PublishResult(success=False, error_message=...)` so the caller can
        surface it on `ai_jobs.error_message` per docs/AI_WORKFLOW.md
        ("خطاهای اتوماسیون هرگز silent fail نیستند"). Let only genuinely
        unexpected/programmer errors propagate.
        """
        raise NotImplementedError
