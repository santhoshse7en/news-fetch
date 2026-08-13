"""Optional async fetch support (requires httpx)."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from newsfetch.client.proxy import ProxyMap, ProxyRotator
from newsfetch.config import Config, ProgressCallback
from newsfetch.errors import ExtractionError, FetchError
from newsfetch.extract.pipeline import Extractor
from newsfetch.models.article import Article


def _config_from_kwargs(**config_kwargs) -> Config:
    fields = set(Config.__dataclass_fields__)
    return Config(**{k: v for k, v in config_kwargs.items() if k in fields})


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
            ) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise FetchError(
                        f"HTTP {resp.status_code} for {url}",
                        url=str(resp.url),
                        status=resp.status_code,
                    )
                html = resp.content
                url = str(resp.url)
        except FetchError:
            raise
        except Exception as exc:
            raise FetchError(f"Failed to fetch URL: {exc}", url=url) from exc

    article = extractor.extract(html, url)
    if not article.title and not article.text:
        raise ExtractionError(f"Could not extract article content from {url}")
    return article


async def fetch_many_async(
    urls: Sequence[str],
    *,
    max_concurrency: int = 8,
    proxy: str | dict | None = None,
    proxies: str | dict | Sequence | None = None,
    request_delay: float | None = None,
    on_progress: ProgressCallback | None = None,
    **config_kwargs,
) -> list[Article | None]:
    """Fetch many URLs concurrently with asyncio + optional proxy pool."""
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
    results: list[Article | None] = [None] * total
    done = 0
    lock = asyncio.Lock()

    client_kwargs = {
        "headers": config.request_headers(),
        "timeout": config.timeout,
        "follow_redirects": True,
        "verify": config.verify_ssl,
        "max_redirects": config.max_redirects,
    }

    async def _one(index: int, u: str) -> None:
        nonlocal done
        async with sem:
            article: Article | None = None
            try:
                if config.request_delay > 0:
                    await asyncio.sleep(config.request_delay)
                # Per-request client so proxy rotation works across httpx versions
                async with httpx.AsyncClient(
                    **client_kwargs,
                    proxy=_pick_proxy(config, rotator),
                ) as client:
                    resp = await client.get(u)
                if resp.status_code >= 400:
                    raise FetchError(
                        f"HTTP {resp.status_code} for {u}",
                        url=str(resp.url),
                        status=resp.status_code,
                    )
                article = extractor.extract(resp.content, str(resp.url))
                if not article.title and not article.text:
                    article = None
            except Exception:
                article = None
            results[index] = article
            async with lock:
                done += 1
                current = done
            if on_progress is not None:
                on_progress(current, total, u, article)

    await asyncio.gather(*(_one(i, u) for i, u in enumerate(urls)))
    return results
