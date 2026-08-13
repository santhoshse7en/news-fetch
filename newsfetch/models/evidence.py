"""Evidence, confidence, and field-level extraction provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    """One piece of extraction evidence for a field."""

    field: str
    strategy: str
    value: Any
    score: float
    source: str = ""
    signals: dict[str, Any] = field(default_factory=dict)

    def label(self) -> str:
        return self.source or self.strategy


@dataclass
class FieldExtraction:
    """Selected value for a field plus supporting evidence."""

    strategy: str | None = None
    source: str | None = None
    score: float = 0.0
    confidence: float = 0.0
    value: Any = None
    signals: dict[str, Any] = field(default_factory=dict)
    candidates: int = 0
    agreements: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractionReport:
    """Per-field extraction provenance for an article."""

    title: FieldExtraction = field(default_factory=FieldExtraction)
    description: FieldExtraction = field(default_factory=FieldExtraction)
    content: FieldExtraction = field(default_factory=FieldExtraction)
    authors: FieldExtraction = field(default_factory=FieldExtraction)
    date: FieldExtraction = field(default_factory=FieldExtraction)
    image: FieldExtraction = field(default_factory=FieldExtraction)
    publisher: FieldExtraction = field(default_factory=FieldExtraction)
    canonical_url: FieldExtraction = field(default_factory=FieldExtraction)

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in asdict(self).items()}


@dataclass
class Confidence:
    """Field-level and overall extraction confidence (0.0–1.0)."""

    title: float = 0.0
    content: float = 0.0
    date: float = 0.0
    authors: float = 0.0
    image: float = 0.0
    publisher: float = 0.0
    description: float = 0.0
    page_type: float = 0.0
    overall: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def below(self, threshold: float, *, fields: list[str] | None = None) -> list[str]:
        """Return field names whose confidence is below ``threshold``."""
        check = fields or ["title", "content", "date", "authors", "image", "publisher", "description"]
        failed: list[str] = []
        for name in check:
            if getattr(self, name, 0.0) < threshold:
                failed.append(name)
        return failed
