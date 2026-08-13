"""Optional Playwright HTML render fallback."""

from __future__ import annotations


def render_html(url: str, *, timeout: float = 30.0, wait_until: str = "domcontentloaded") -> bytes:
    """Fetch a page with a headless browser. Requires ``pip install news-fetch[browser]``."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "Browser rendering requires Playwright. Install with: "
            "pip install news-fetch[browser] && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until=wait_until, timeout=int(timeout * 1000))
            content = page.content()
            return content.encode("utf-8")
        finally:
            browser.close()
