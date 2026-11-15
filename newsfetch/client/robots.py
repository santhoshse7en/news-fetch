"""robots.txt politeness helper (RFC 9309)."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from urllib.parse import quote, unquote, urlparse

from newsfetch.client.http import HttpClient
from newsfetch.config import Config
from newsfetch.errors import FetchError

# RFC 9309 §2.5: crawlers must parse at least 500 KiB; anything beyond may be ignored
_MAX_ROBOTS_BYTES = 500 * 1024
_PRODUCT_TOKEN_RE = re.compile(r"[A-Za-z_-]+")
# Characters left as-is when normalizing percent-encoding (incl. the * and $ pattern operators)
_SAFE_CHARS = "!$&'()*+,/:;=?@-._~"


def _normalize(value: str) -> str:
    return quote(unquote(value), safe=_SAFE_CHARS)


def product_token(user_agent: str) -> str:
    """``"news-fetch/1.1 (+https://…)"`` → ``"news-fetch"``."""
    match = _PRODUCT_TOKEN_RE.match(user_agent.strip())
    return match.group(0).lower() if match else "*"


@dataclass(frozen=True)
class _Rule:
    allow: bool
    pattern: str
    regex: re.Pattern[str]


def _compile(pattern: str) -> re.Pattern[str]:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile(regex + (r"\Z" if anchored else ""))


@dataclass
class _Group:
    agents: list[str] = field(default_factory=list)
    rules: list[_Rule] = field(default_factory=list)


class RobotsRules:
    """Parsed robots.txt rules with RFC 9309 matching."""

    def __init__(self, groups: list[_Group]) -> None:
        self._groups = groups

    @classmethod
    def parse(cls, text: str) -> RobotsRules:
        groups: list[_Group] = []
        current: _Group | None = None
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                # Consecutive user-agent lines share one group; a user-agent after rules starts a new one
                if current is None or current.rules:
                    current = _Group()
                    groups.append(current)
                current.agents.append(value.lower())
            elif key in {"allow", "disallow"} and current is not None:
                if not value:
                    continue  # empty pattern matches nothing (RFC 9309 §2.2.2)
                pattern = _normalize(value)
                current.rules.append(_Rule(key == "allow", pattern, _compile(pattern)))
        return cls(groups)

    def _rules_for(self, token: str) -> list[_Rule]:
        # All groups naming the product token are combined; otherwise fall back to "*" groups
        for wanted in (token, "*"):
            rules = [r for g in self._groups if wanted in g.agents for r in g.rules]
            if rules or any(wanted in g.agents for g in self._groups):
                return rules
        return []

    def allowed(self, user_agent: str, url: str) -> bool:
        parts = urlparse(url)
        path = parts.path or "/"
        if path == "/robots.txt":
            return True
        target = _normalize(path + (f"?{parts.query}" if parts.query else ""))

        best: _Rule | None = None
        for rule in self._rules_for(product_token(user_agent)):
            if not rule.regex.match(target):
                continue
            # Longest pattern wins; on a tie, allow wins (RFC 9309 §2.2.2)
            if (
                best is None
                or len(rule.pattern) > len(best.pattern)
                or (len(rule.pattern) == len(best.pattern) and rule.allow and not best.allow)
            ):
                best = rule
        return best is None or best.allow


@dataclass(frozen=True)
class RobotsDecision:
    allowed: bool
    reason: str


class RobotsCache:
    """Per-origin robots.txt cache.

    Status handling follows RFC 9309 §2.3.1: 4xx → no restrictions; 5xx, 429 or a network
    error → robots.txt unreachable → everything disallowed.
    """

    def __init__(
        self,
        user_agent: str,
        *,
        timeout: float = 10.0,
        client: HttpClient | None = None,
    ) -> None:
        self.user_agent = user_agent
        self._client = client or HttpClient(Config(user_agent=user_agent, timeout=timeout))
        self._policies: dict[str, RobotsRules | RobotsDecision] = {}
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
        return self.check(url).allowed

    def check(self, url: str) -> RobotsDecision:
        parts = urlparse(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return RobotsDecision(True, "not an http(s) URL")
        origin = f"{parts.scheme}://{parts.netloc.lower()}"
        with self._lock:
            policy = self._policies.get(origin)
        if policy is None:
            # Fetch outside the lock so slow hosts don't block other origins
            policy = self._load(origin)
            with self._lock:
                policy = self._policies.setdefault(origin, policy)
        if isinstance(policy, RobotsDecision):
            return policy
        if policy.allowed(self.user_agent, url):
            return RobotsDecision(True, "allowed by robots.txt")
        return RobotsDecision(False, "disallowed by robots.txt")

    def _load(self, origin: str) -> RobotsRules | RobotsDecision:
        try:
            resp = self._client.get(f"{origin}/robots.txt", max_bytes=_MAX_ROBOTS_BYTES, truncate=True)
        except FetchError as exc:
            if exc.status is not None and 400 <= exc.status < 500 and exc.status != 429:
                return RobotsDecision(True, f"robots.txt unavailable (HTTP {exc.status})")
            detail = f"HTTP {exc.status}" if exc.status is not None else "network error"
            return RobotsDecision(False, f"robots.txt unreachable ({detail})")
        return RobotsRules.parse(resp.text)
