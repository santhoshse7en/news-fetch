"""Public high-level API."""

from __future__ import annotations

import time
from collections.abc import Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from newsfetch.client.cache import DiskCache
from newsfetch.client.http import HttpClient
from newsfetch.client.robots import RobotsCache
from newsfetch.config import Config, ProgressCallback
from newsfetch.discover import discover as discover_site
from newsfetch.errors import ExtractionError, FetchError, LowConfidenceExtractionError
from newsfetch.extract.pipeline import Extractor
from newsfetch.models.article import Article
from newsfetch.strategies.plugin import ExtractionStrategy


def _config_from_kwargs(**config_kwargs) -> Config:
    fields = set(Config.__dataclass_fields__)
    return Config(**{k: v for k, v in config_kwargs.items() if k in fields})


class NewsFetcher:
    """Configurable news article fetcher and extractor."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._client = HttpClient(self.config)
        self._extractor = Extractor(self.config)
        self._cache = (
            DiskCache(self.config.cache_path, ttl=self.config.cache_ttl)
            if self.config.cache
            else None
        )
        self._robots = (
            RobotsCache(self.config.user_agent, timeout=self.config.timeout)
            if self.config.respect_robots
            else None
        )

    def register_strategy(self, strategy: ExtractionStrategy) -> None:
        """Register a custom extraction strategy on this fetcher."""
        self._extractor.register_strategy(strategy)

    def fetch(self, url: str, *, html: str | bytes | None = None) -> Article:
        """Fetch and extract an article.

        Pass ``html`` to skip the network and run extraction only.
        """
        final_url = url
        used_cache = False

        if html is None:
            if self._robots is not None and not self._robots.allowed(url):
                raise FetchError(f"Blocked by robots.txt: {url}", url=url, status=403)

            if self._cache is not None:
                cached = self._cache.get(url)
                if cached is not None:
                    html = cached
                    used_cache = True

            if html is None:
                if self.config.request_delay > 0:
                    time.sleep(self.config.request_delay)
                if self.config.render:
                    from newsfetch.client.browser import render_html

                    html = render_html(url, timeout=self.config.timeout)
                    final_url = url
                else:
                    response = self._client.get(url)
                    html = response.content
                    final_url = response.url
                if self._cache is not None:
                    self._cache.set(url, html if isinstance(html, bytes) else html.encode("utf-8"))

        article = self._extractor.extract(html, final_url)

        if (
            not used_cache
            and not self.config.render
            and self.config.browser_fallback
            and article.confidence.overall < self.config.render_min_confidence
        ):
            try:
                from newsfetch.client.browser import render_html

                rendered = render_html(final_url, timeout=self.config.timeout)
                article = self._extractor.extract(rendered, final_url)
                article.metadata["rendered"] = True
            except ImportError:
                pass

        if not article.title and not article.text:
            raise ExtractionError(f"Could not extract article content from {final_url}")
        return article

    def fetch_many(
        self,
        urls: Sequence[str],
        *,
        max_workers: int | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> list[Article | None]:
        """Fetch many URLs concurrently. Failures become ``None``."""
        workers = max_workers or self.config.max_workers
        total = len(urls)
        results: list[Article | None] = [None] * total

        def _one(index: int, u: str) -> tuple[int, str, Article | None]:
            try:
                article = self.fetch(u)
            except (FetchError, ExtractionError, Exception):
                article = None
            return index, u, article

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_one, i, u) for i, u in enumerate(urls)]
            done = 0
            for fut in as_completed(futures):
                index, u, article = fut.result()
                results[index] = article
                done += 1
                if on_progress is not None:
                    on_progress(done, total, u, article)

        return results

    def iter_fetch(
        self,
        urls: Sequence[str],
        *,
        max_workers: int | None = None,
    ) -> Iterator[tuple[str, Article | None]]:
        """Yield ``(url, article_or_none)`` as each request completes (unordered)."""
        workers = max_workers or self.config.max_workers

        def _one(u: str) -> tuple[str, Article | None]:
            try:
                return u, self.fetch(u)
            except (FetchError, ExtractionError, Exception):
                return u, None

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_one, u) for u in urls]
            for fut in as_completed(futures):
                yield fut.result()

    def discover(self, site_url: str, *, limit: int | None = 50) -> list[dict]:
        return discover_site(site_url, limit=limit, timeout=self.config.timeout)

    def close(self) -> None:
        self._client.close()
        if self._cache is not None:
            self._cache.close()

    def __enter__(self) -> NewsFetcher:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def fetch(
    url: str,
    *,
    debug: bool = False,
    html: str | bytes | None = None,
    proxy: str | dict | None = None,
    proxies: str | dict | Sequence | None = None,
    strict: bool | None = None,
    min_confidence: float | None = None,
    **config_kwargs,
) -> Article:
    """Fetch a single article with optional config overrides."""
    if proxy is not None:
        config_kwargs["proxy"] = proxy
    if proxies is not None:
        config_kwargs["proxies"] = proxies
    if strict is not None:
        config_kwargs["strict"] = strict
    if min_confidence is not None:
        config_kwargs["min_confidence"] = min_confidence
    cfg = _config_from_kwargs(debug=debug, **config_kwargs)
    with NewsFetcher(cfg) as fetcher:
        return fetcher.fetch(url, html=html)


def fetch_many(
    urls: Sequence[str],
    *,
    max_workers: int = 8,
    proxy: str | dict | None = None,
    proxies: str | dict | Sequence | None = None,
    request_delay: float | None = None,
    on_progress: ProgressCallback | None = None,
    **config_kwargs,
) -> list[Article | None]:
    """Fetch many URLs. Supports proxy pools, delay, and progress callbacks."""
    if proxy is not None:
        config_kwargs["proxy"] = proxy
    if proxies is not None:
        config_kwargs["proxies"] = proxies
    if request_delay is not None:
        config_kwargs["request_delay"] = request_delay
    cfg = _config_from_kwargs(max_workers=max_workers, **config_kwargs)
    with NewsFetcher(cfg) as fetcher:
        return fetcher.fetch_many(urls, max_workers=max_workers, on_progress=on_progress)


def fetch_iter(
    urls: Sequence[str],
    *,
    max_workers: int = 8,
    **config_kwargs,
) -> Iterator[tuple[str, Article | None]]:
    """Stream ``(url, article_or_none)`` results without materializing the full list."""
    cfg = _config_from_kwargs(max_workers=max_workers, **config_kwargs)
    with NewsFetcher(cfg) as fetcher:
        yield from fetcher.iter_fetch(urls, max_workers=max_workers)


def extract(
    html: str | bytes,
    url: str = "https://example.com/",
    *,
    debug: bool = False,
    strict: bool = False,
    min_confidence: float = 0.0,
    **config_kwargs,
) -> Article:
    """Extract an article from HTML without making a network request."""
    return fetch(
        url,
        html=html,
        debug=debug,
        strict=strict,
        min_confidence=min_confidence,
        **config_kwargs,
    )


discover = discover_site

__all__ = [
    "NewsFetcher",
    "discover",
    "extract",
    "fetch",
    "fetch_iter",
    "fetch_many",
    "LowConfidenceExtractionError",
]
