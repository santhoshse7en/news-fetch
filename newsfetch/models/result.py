"""Per-URL outcome for bulk fetching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from newsfetch.models.article import Article


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Outcome of fetching one URL: an ``article`` on success, otherwise the ``error`` raised.

    Returned by ``fetch_results`` / ``iter_results`` (and their async and ``NewsFetcher``
    counterparts) so bulk callers can see *why* a URL failed instead of a bare ``None``.
    """

    url: str
    article: Article | None = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.article is not None and self.error is None

    @property
    def status(self) -> int | None:
        """HTTP status for ``FetchError`` failures, when known."""
        return getattr(self.error, "status", None)

    def unwrap(self) -> Article:
        """Return the article, or raise the captured error."""
        if self.error is not None:
            raise self.error
        if self.article is None:  # pragma: no cover - constructed without either
            raise ValueError(f"No article or error recorded for {self.url}")
        return self.article

    def error_dict(self) -> dict[str, Any] | None:
        if self.error is None:
            return None
        return {"type": type(self.error).__name__, "message": str(self.error), "status": self.status}

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "ok": self.ok,
            "article": self.article.to_dict() if self.article is not None else None,
            "error": self.error_dict(),
        }
