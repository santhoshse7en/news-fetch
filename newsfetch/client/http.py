"""HTTP client for news-fetch."""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from requests.compat import chardet
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


_CHUNK_SIZE = 64 * 1024


def _read_limited(resp: requests.Response, limit: int | None, *, truncate: bool = False) -> bytes:
    """Read a streamed body, enforcing ``limit`` on decompressed bytes (guards gzip bombs)."""
    if limit and not truncate:
        declared = resp.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > limit:
            raise FetchError(
                f"Response too large ({declared} bytes > max_bytes={limit})",
                url=str(resp.url),
                status=resp.status_code,
            )
    buf = bytearray()
    for chunk in resp.iter_content(_CHUNK_SIZE):
        buf += chunk
        if limit and len(buf) > limit:
            if truncate:
                del buf[limit:]
                break
            raise FetchError(
                f"Response too large (> max_bytes={limit})",
                url=str(resp.url),
                status=resp.status_code,
            )
    return bytes(buf)


class HttpClient:
    """Synchronous HTTP client with retries, proxies, and sensible defaults."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._session = requests.Session()
        # urllib3 retries 5xx only; connection errors and 429 are retried by the loop in get(),
        # otherwise the two layers multiply ((retries + 1) ** 2 attempts)
        retry = Retry(
            total=max(0, self.config.retries),
            connect=0,
            read=0,
            other=0,
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

    def get(
        self,
        url: str,
        *,
        proxies: ProxyMap | None = None,
        max_bytes: int | None = None,
        truncate: bool = False,
    ) -> Response:
        """GET ``url``.

        ``max_bytes`` overrides ``Config.max_bytes`` for this call (0 = unlimited). Bodies over
        the limit raise ``FetchError``, or are cut at the limit when ``truncate`` is true.
        """
        chosen = proxies if proxies is not None else self._select_proxies()
        limit = self.config.max_bytes if max_bytes is None else max_bytes
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
                    stream=True,
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise FetchError(f"Failed to fetch URL: {exc}", url=url) from exc
                time.sleep(0.3 * (attempt + 1))
                continue

            with resp:
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

                try:
                    content = _read_limited(resp, limit, truncate=truncate)
                except requests.RequestException as exc:
                    last_error = exc
                    if attempt + 1 >= attempts:
                        raise FetchError(f"Failed to read response: {exc}", url=url) from exc
                    time.sleep(0.3 * (attempt + 1))
                    continue

            encoding = resp.encoding
            if not encoding or encoding.lower() == "iso-8859-1":
                detected = chardet.detect(content).get("encoding") if content and chardet else None
                encoding = detected or "utf-8"
            try:
                text = content.decode(encoding, errors="replace")
            except LookupError:
                encoding = "utf-8"
                text = content.decode(encoding, errors="replace")

            return Response(
                url=str(resp.url),
                status_code=resp.status_code,
                content=content,
                text=text,
                encoding=encoding,
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
