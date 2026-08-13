"""Exception hierarchy for news-fetch."""

from __future__ import annotations

from typing import Any


class NewsFetchError(Exception):
    """Base error for news-fetch."""


class FetchError(NewsFetchError):
    """HTTP or transport failure."""

    def __init__(self, message: str, *, url: str | None = None, status: int | None = None):
        super().__init__(message)
        self.url = url
        self.status = status


class ParseError(NewsFetchError):
    """HTML could not be parsed into a usable document."""


class ExtractionError(NewsFetchError):
    """Extraction failed to produce a usable article."""


class LowConfidenceExtractionError(ExtractionError):
    """Strict mode rejected an extraction below confidence thresholds."""

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        confidence: Any = None,
        failed_fields: list[str] | None = None,
        article: Any = None,
    ):
        super().__init__(message)
        self.url = url
        self.confidence = confidence
        self.failed_fields = failed_fields or []
        self.article = article


class DiscoveryError(NewsFetchError):
    """Site discovery (feeds/sitemaps) failed."""
