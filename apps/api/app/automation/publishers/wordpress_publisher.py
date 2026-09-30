"""Playwright automation for a self-hosted WordPress blog — the default
(and, for this MVP, only) `<platform>_publisher.py` from
docs/PROJECT_STRUCTURE.md, since guest-post blog networks are
overwhelmingly WordPress in practice.

**Known limitation**: this drives the classic editor's "Text" (raw HTML)
mode, not the Gutenberg block editor introduced in WP 5.0 — Gutenberg's
`contenteditable` blocks don't have stable, theme-independent selectors to
automate generically. Many guest-post/SEO blog networks still run the
Classic Editor plugin or an older WP version for exactly this kind of
automation, but confirm that's true for a given `blog_platforms` row
before trusting it in production; this is best-effort site automation, not
a certified integration.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.automation.publishers.base_publisher import BasePublisher, PublishPayload, PublishResult

_NAV_TIMEOUT_MS = 30_000


class WordPressPublisher(BasePublisher):
    def publish(self, payload: PublishPayload) -> PublishResult:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.set_default_timeout(_NAV_TIMEOUT_MS)
                    return self._publish_with_page(page, payload)
                finally:
                    browser.close()
        except PlaywrightTimeoutError as exc:
            return PublishResult(success=False, error_message=f"Timed out waiting for a page element: {exc}")
        except Exception as exc:  # noqa: BLE001 - see base_publisher.py's docstring
            return PublishResult(success=False, error_message=f"Automation error: {exc}")

    def _publish_with_page(self, page, payload: PublishPayload) -> PublishResult:
        login_ok = self._login(page, payload)
        if not login_ok:
            return PublishResult(success=False, error_message="Login failed — check the blog's credentials.")

        admin_base = payload.login_url.rsplit("/wp-login.php", 1)[0]
        page.goto(f"{admin_base}/wp-admin/post-new.php")

        page.fill("#title", payload.title)

        # Classic editor: switch from the visual (TinyMCE) tab to "Text"
        # (raw HTML) before filling the textarea — filling it under the
        # visual tab writes to a hidden element WordPress ignores.
        text_tab = page.locator("#content-html")
        if text_tab.count() > 0:
            text_tab.click()
        page.fill("#content", payload.content_html)

        if payload.category:
            self._try_check_category(page, payload.category)

        page.click("#publish")

        try:
            page.wait_for_selector("#message a, .notice a", timeout=_NAV_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            return PublishResult(
                success=False,
                error_message="Clicked Publish but no confirmation link appeared — the post may not have been published.",
            )

        published_url = page.locator("#message a, .notice a").first.get_attribute("href")
        if not published_url:
            return PublishResult(success=False, error_message="Published, but couldn't read the post's URL back.")

        return PublishResult(success=True, published_url=published_url)

    def _login(self, page, payload: PublishPayload) -> bool:
        page.goto(payload.login_url)
        page.fill("#user_login", payload.username)
        page.fill("#user_pass", payload.password)
        page.click("#wp-submit")
        try:
            page.wait_for_selector("#wpadminbar", timeout=_NAV_TIMEOUT_MS)
            return True
        except PlaywrightTimeoutError:
            return False

    def _try_check_category(self, page, category: str) -> None:
        # Best-effort: WP categories are a checkbox list, not a <select>,
        # and label text varies by theme/locale — a miss here just means
        # the post publishes uncategorized rather than failing the job.
        checkbox = page.get_by_label(category, exact=False)
        if checkbox.count() > 0:
            checkbox.first.check()
