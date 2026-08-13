"""Configuration for news-fetch."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from newsfetch.client.proxy import ProxyMap, ProxyRotator, normalize_proxies


@dataclass
class Config:
    """Runtime configuration for fetching and extraction."""

    timeout: float = 15.0
    max_redirects: int = 10
    user_agent: str = (
        "news-fetch/1.0 (+https://github.com/santhoshse7en/news-fetch)"
    )
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    language: str | None = None
    debug: bool = False
    max_workers: int = 8
    strip_tracking_params: bool = True
    min_text_length: int = 50

    # Networking / scale
    proxy: str | ProxyMap | None = None
    proxies: str | ProxyMap | Sequence[str] | Sequence[ProxyMap] | None = None
    rotate_proxies: bool = True
    request_delay: float = 0.0
    retries: int = 2

    # Confidence / strict mode
    strict: bool = False
    min_confidence: float = 0.0
    min_content_confidence: float | None = None
    min_title_confidence: float | None = None
    require_article_page: bool = False

    # Politeness / cache / browser
    respect_robots: bool = False
    cache: bool = False
    cache_path: str = ".news-fetch-cache.sqlite"
    cache_ttl: int = 86400
    render: bool = False
    browser_fallback: bool = False
    render_min_confidence: float = 0.55

    def request_headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        }
        headers.update(self.headers)
        return headers

    def proxy_pool(self) -> list[ProxyMap]:
        return normalize_proxies(proxy=self.proxy, proxies=self.proxies)

    def proxy_rotator(self) -> ProxyRotator:
        return ProxyRotator(self.proxy_pool())


# Progress callback: (completed_index, total, url, article_or_none)
ProgressCallback = Callable[[int, int, str, Any], None]
