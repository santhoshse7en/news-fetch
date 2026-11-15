"""Optional async fetch support (requires httpx)."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from newsfetch.api import _config_from_kwargs
from newsfetch.client.proxy import ProxyMap, ProxyRotator
from newsfetch.config import Config, ProgressCallback
from newsfetch.errors import ExtractionError, FetchError
from newsfetch.extract.pipeline import Extractor
from newsfetch.models.article import Article
from newsfetch.models.result import FetchResult


async def _read_limited(resp, limit: int | None) -> bytes:
    """Read a streamed httpx body, enforcing ``limit`` on decompressed bytes."""
    declared = resp.headers.get("content-length")
    if limit and declared and declared.isdigit() and int(declared) > limit:
        raise FetchError(
            f"Response too large ({declared} bytes > max_bytes={limit})",
            url=str(resp.url),
            status=resp.status_code,
        )
    buf = bytearray()
    async for chunk in resp.aiter_bytes():
        buf += chunk
        if limit and len(buf) > limit:
            raise FetchError(
                f"Response too large (> max_bytes={limit})",
                url=str(resp.url),
                status=resp.status_code,
            )
    return bytes(buf)


def _pick_proxy(config: Config, rotator: ProxyRotator) -> str | None:
    if not rotator:
        return None
    chosen: ProxyMap | None
    if config.rotate_proxies and rotator.pool_size > 1:
        chosen = rotator.next()
    else:
        chosen = rotator.fixed()
    if not chosen:
        return None
    return chosen.get("https") or chosen.get("http")


async def fetch_async(
    url: str,
    *,
    debug: bool = False,
    html: str | bytes | None = None,
    proxy: str | dict | None = None,
    proxies: str | dict | Sequence | None = None,
    **config_kwargs,
) -> Article:
    """Async variant of ``fetch``. Requires the ``async`` extra (httpx)."""
    if proxy is not None:
        config_kwargs["proxy"] = proxy
    if proxies is not None:
        config_kwargs["proxies"] = proxies
    config = _config_from_kwargs(debug=debug, **config_kwargs)
    extractor = Extractor(config)
    rotator = config.proxy_rotator()

    if html is None:
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "Async support requires httpx. Install with: pip install news-fetch[async]"
            ) from exc

        if config.request_delay > 0:
            await asyncio.sleep(config.request_delay)

        try:
            async with httpx.AsyncClient(
                headers=config.request_headers(),
                timeout=config.timeout,
                follow_redirects=True,
                verify=config.verify_ssl,
                max_redirects=config.max_redirects,
                proxy=_pick_proxy(config, rotator),
            ) as client, client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    raise FetchError(
                        f"HTTP {resp.status_code} for {url}",
                        url=str(resp.url),
                        status=resp.status_code,
                    )
                html = await _read_limited(resp, config.max_bytes)
                url = str(resp.url)
        except FetchError:
            raise
        except Exception as exc:
            raise FetchError(f"Failed to fetch URL: {exc}", url=url) from exc

    article = extractor.extract(html, url)
    if not article.title and not article.text:
        raise ExtractionError(f"Could not extract article content from {url}")
    return article


async def fetch_results_async(
    urls: Sequence[str],
    *,
    max_concurrency: int = 8,
    proxy: str | dict | None = None,
    proxies: str | dict | Sequence | None = None,
    request_delay: float | None = None,
    on_progress: ProgressCallback | None = None,
    **config_kwargs,
) -> list[FetchResult]:
    """Fetch many URLs concurrently; one :class:`FetchResult` per URL, in input order.

    ``on_progress(done, total, url, result)`` receives the ``FetchResult``.
    """
    try:
        import httpx
    except ImportError as exc:
        raise ImportError(
            "Async support requires httpx. Install with: pip install news-fetch[async]"
        ) from exc

    if proxy is not None:
        config_kwargs["proxy"] = proxy
    if proxies is not None:
        config_kwargs["proxies"] = proxies
    if request_delay is not None:
        config_kwargs["request_delay"] = request_delay

    config = _config_from_kwargs(**config_kwargs)
    extractor = Extractor(config)
    rotator = config.proxy_rotator()
    sem = asyncio.Semaphore(max_concurrency)
    total = len(urls)
    results: list[FetchResult | None] = [None] * total
    done = 0

    client_kwargs = {
        "headers": config.request_headers(),
        "timeout": config.timeout,
        "follow_redirects": True,
        "verify": config.verify_ssl,
        "max_redirects": config.max_redirects,
    }

    async def _fetch(u: str) -> Article:
        if config.request_delay > 0:
            await asyncio.sleep(config.request_delay)
        # Per-request client so proxy rotation works across httpx versions
        async with httpx.AsyncClient(
            **client_kwargs,
            proxy=_pick_proxy(config, rotator),
        ) as client, client.stream("GET", u) as resp:
            if resp.status_code >= 400:
                raise FetchError(
                    f"HTTP {resp.status_code} for {u}",
                    url=str(resp.url),
                    status=resp.status_code,
                )
            body = await _read_limited(resp, config.max_bytes)
            final_url = str(resp.url)
        article = extractor.extract(body, final_url)
        if not article.title and not article.text:
            raise ExtractionError(f"Could not extract article content from {final_url}")
        return article

    async def _one(index: int, u: str) -> None:
        nonlocal done
        async with sem:
            try:
                result = FetchResult(u, article=await _fetch(u))
            except httpx.HTTPError as exc:
                result = FetchResult(u, error=FetchError(f"Failed to fetch URL: {exc}", url=u))
            except Exception as exc:
                result = FetchResult(u, error=exc)
        results[index] = result
        done += 1  # single event loop thread: no lock needed
        if on_progress is not None:
            on_progress(done, total, u, result)

    async with asyncio.TaskGroup() as tg:
        for i, u in enumerate(urls):
            tg.create_task(_one(i, u))
    return [r for r in results if r is not None]


async def fetch_many_async(
    urls: Sequence[str],
    *,
    max_concurrency: int = 8,
    on_progress: ProgressCallback | None = None,
    **kwargs,
) -> list[Article | None]:
    """Fetch many URLs concurrently. Failures become ``None`` (see :func:`fetch_results_async`)."""
    progress = None
    if on_progress is not None:

        def progress(done: int, total: int, url: str, result: FetchResult) -> None:
            on_progress(done, total, url, result.article)

    results = await fetch_results_async(urls, max_concurrency=max_concurrency, on_progress=progress, **kwargs)
    return [r.article for r in results]
