"""HTTP client for news-fetch."""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from newsfetch.client.proxy import ProxyMap
from newsfetch.config import Config
from newsfetch.errors import FetchError


@dataclass
class Response:
    """Normalized HTTP response."""

    url: str
    status_code: int
    content: bytes
    text: str
    encoding: str | None
    headers: dict[str, str]
    proxy: ProxyMap | None = None


class HttpClient:
    """Synchronous HTTP client with retries, proxies, and sensible defaults."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._session = requests.Session()
        retry = Retry(
            total=max(0, self.config.retries),
            backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update(self.config.request_headers())
        self._session.max_redirects = self.config.max_redirects
        self._rotator = self.config.proxy_rotator()

        if self._rotator and not self.config.rotate_proxies:
            fixed = self._rotator.fixed()
            if fixed:
                self._session.proxies.update(fixed)

    def _select_proxies(self) -> ProxyMap | None:
        if not self._rotator:
            return None
        if self.config.rotate_proxies and self._rotator.pool_size > 1:
            return self._rotator.next()
        return self._rotator.fixed()

    def get(self, url: str, *, proxies: ProxyMap | None = None) -> Response:
        chosen = proxies if proxies is not None else self._select_proxies()
        attempts = max(1, self.config.retries + 1)
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                resp = self._session.get(
                    url,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl,
                    allow_redirects=True,
                    proxies=chosen,
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise FetchError(f"Failed to fetch URL: {exc}", url=url) from exc
                time.sleep(0.3 * (attempt + 1))
                continue

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "1")
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = 1.0
                delay = min(max(delay, 0.5), 60.0)
                if attempt + 1 >= attempts:
                    raise FetchError(
                        f"HTTP 429 for {url}",
                        url=str(resp.url),
                        status=429,
                    )
                time.sleep(delay)
                continue

            if resp.status_code >= 400:
                raise FetchError(
                    f"HTTP {resp.status_code} for {url}",
                    url=str(resp.url),
                    status=resp.status_code,
                )

            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"

            return Response(
                url=str(resp.url),
                status_code=resp.status_code,
                content=resp.content,
                text=resp.text,
                encoding=resp.encoding,
                headers={k.lower(): v for k, v in resp.headers.items()},
                proxy=chosen,
            )

        raise FetchError(f"Failed to fetch URL: {last_error}", url=url)

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
