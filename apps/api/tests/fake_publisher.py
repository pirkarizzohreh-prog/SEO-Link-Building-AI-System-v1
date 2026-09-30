"""A canned-response BasePublisher for tests — no real browser, no network.
Mirrors tests/fake_llm_client.py's role for BaseLLMClient.
"""

from __future__ import annotations

from app.automation.publishers.base_publisher import BasePublisher, PublishPayload, PublishResult


class FakePublisher(BasePublisher):
    def __init__(self, result: PublishResult) -> None:
        self._result = result
        self.calls: list[PublishPayload] = []

    def publish(self, payload: PublishPayload) -> PublishResult:
        self.calls.append(payload)
        return self._result
