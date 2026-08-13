"""Public article model and extraction provenance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from newsfetch.models.evidence import Confidence, ExtractionReport


@dataclass(frozen=True)
class FieldSource:
    """Where a field value came from."""

    strategy: str
    detail: str = ""

    def __str__(self) -> str:
        return f"{self.strategy}:{self.detail}" if self.detail else self.strategy


@dataclass
class CandidateTrace:
    """One extraction candidate considered for a field."""

    field: str
    value: Any
    source: str
    score: float
    selected: bool = False
    confidence: float | None = None


@dataclass
class ExtractionTrace:
    """Debug information about an extraction run."""

    candidates: list[CandidateTrace] = field(default_factory=list)
    strategies_tried: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    page_type_reasons: list[str] = field(default_factory=list)

    def add(
        self,
        field: str,
        value: Any,
        source: str,
        score: float,
        *,
        selected: bool = False,
        confidence: float | None = None,
    ) -> None:
        self.candidates.append(
            CandidateTrace(
                field=field,
                value=value,
                source=source,
                score=score,
                selected=selected,
                confidence=confidence,
            )
        )


@dataclass
class Article:
    """Structured news article produced by the extraction engine."""

    url: str
    canonical_url: str | None = None
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    text: str | None = None
    html: str | None = None
    authors: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    modified_at: datetime | None = None
    publisher: str | None = None
    language: str | None = None
    image: str | None = None
    images: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    section: str | None = None
    summary: str | None = None
    word_count: int = 0
    reading_time_minutes: int = 0
    page_type: str = "unknown"
    is_article: bool = True
    sources: dict[str, str] = field(default_factory=dict)
    confidence: Confidence = field(default_factory=Confidence)
    extraction: ExtractionReport = field(default_factory=ExtractionReport)
    metadata: dict[str, Any] = field(default_factory=dict)
    trace: ExtractionTrace | None = None

    @property
    def title_source(self) -> str | None:
        return self.sources.get("title")

    @property
    def date_source(self) -> str | None:
        return self.sources.get("published_at")

    @property
    def content_source(self) -> str | None:
        return self.sources.get("text")

    @property
    def image_source(self) -> str | None:
        return self.sources.get("image")

    @property
    def authors_source(self) -> str | None:
        return self.sources.get("authors")

    @property
    def title_confidence(self) -> float:
        return self.confidence.title

    @property
    def content_confidence(self) -> float:
        return self.confidence.content

    @property
    def date_confidence(self) -> float:
        return self.confidence.date

    @property
    def author_confidence(self) -> float:
        return self.confidence.authors

    @property
    def image_confidence(self) -> float:
        return self.confidence.image

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        data = asdict(self)
        for key in ("published_at", "modified_at"):
            value = data.get(key)
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
