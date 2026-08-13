"""Proxy normalization and optional rotation for bulk scraping."""

from __future__ import annotations

import itertools
import threading
from collections.abc import Iterable, Iterator, Sequence
from typing import Any

ProxyMap = dict[str, str]


def normalize_proxies(
    proxy: str | ProxyMap | None = None,
    proxies: str | ProxyMap | Sequence[str] | None = None,
) -> list[ProxyMap]:
    """Normalize proxy inputs into a list of requests-style proxy maps.

    Accepts:
      - ``proxy="http://user:pass@host:8080"``
      - ``proxies={"http": "...", "https": "..."}``
      - ``proxies=["http://p1:8080", "http://p2:8080"]``  (rotation pool)
    """
    if proxy is not None and proxies is not None:
        raise ValueError("Pass only one of proxy= or proxies=, not both")

    value: Any = proxy if proxy is not None else proxies
    if value is None:
        return []

    if isinstance(value, str):
        return [_map_from_url(value)]

    if isinstance(value, dict):
        return [dict(value)]

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        maps: list[ProxyMap] = []
        for item in value:
            if isinstance(item, str):
                maps.append(_map_from_url(item))
            elif isinstance(item, dict):
                maps.append(dict(item))
            else:
                raise TypeError(f"Unsupported proxy entry type: {type(item)!r}")
        return maps

    raise TypeError(f"Unsupported proxy type: {type(value)!r}")


def _map_from_url(url: str) -> ProxyMap:
    url = url.strip()
    if not url:
        raise ValueError("Proxy URL cannot be empty")
    # requests expects both schemes; socks proxies work the same way when installed
    return {"http": url, "https": url}


class ProxyRotator:
    """Thread-safe round-robin proxy rotator."""

    def __init__(self, proxies: Iterable[ProxyMap]) -> None:
        self._proxies = list(proxies)
        self._lock = threading.Lock()
        self._cycle: Iterator[ProxyMap] | None = (
            itertools.cycle(self._proxies) if self._proxies else None
        )

    def __bool__(self) -> bool:
        return bool(self._proxies)

    @property
    def pool_size(self) -> int:
        return len(self._proxies)

    def next(self) -> ProxyMap | None:
        if self._cycle is None:
            return None
        with self._lock:
            return next(self._cycle)

    def fixed(self) -> ProxyMap | None:
        """Return the first proxy without rotating (single-proxy configs)."""
        return self._proxies[0] if self._proxies else None
