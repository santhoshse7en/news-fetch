"""robots.txt politeness helper."""

from __future__ import annotations

import threading
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests


class RobotsCache:
    """Per-host robots.txt cache."""

    def __init__(self, user_agent: str, *, timeout: float = 10.0) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: dict[str, RobotFileParser | None] = {}
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
        parts = urlparse(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return True
        host_key = f"{parts.scheme}://{parts.netloc.lower()}"
        with self._lock:
            if host_key not in self._parsers:
                self._parsers[host_key] = self._load(host_key)
            parser = self._parsers[host_key]
        if parser is None:
            return True  # fail open if robots unavailable
        return parser.can_fetch(self.user_agent, url)

    def _load(self, origin: str) -> RobotFileParser | None:
        rp = RobotFileParser()
        robots_url = f"{origin}/robots.txt"
        try:
            resp = requests.get(robots_url, timeout=self.timeout)
            if resp.status_code >= 400:
                return None
            rp.parse(resp.text.splitlines())
            return rp
        except Exception:
            return None
