"""Resolves which `BasePublisher` to use — a single default for this MVP
(see wordpress_publisher.py's module docstring). Kept as its own function
(rather than instantiated inline in publish_agent.py) so tests can
monkeypatch it the same way `competitor_intel_agent.py` tests monkeypatch
`fetch_html` — see tests/test_publish_agent.py.
"""

from __future__ import annotations

from app.automation.publishers.base_publisher import BasePublisher
from app.automation.publishers.wordpress_publisher import WordPressPublisher


def get_publisher() -> BasePublisher:
    return WordPressPublisher()
