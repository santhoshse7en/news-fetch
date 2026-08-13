"""Evidence ranking and confidence calculation."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from newsfetch.models.evidence import Confidence, Evidence, ExtractionReport, FieldExtraction
from newsfetch.normalize.date import parse_date
from newsfetch.strategies.base import Candidate

_NAV_TITLE_RE = re.compile(
    r"^(home|news|world|sports|politics|business|search|login|subscribe)$",
    re.I,
)

# Weights for overall confidence
_OVERALL_WEIGHTS = {
    "content": 0.35,
    "title": 0.20,
    "date": 0.15,
    "authors": 0.10,
    "image": 0.08,
    "publisher": 0.07,
    "description": 0.05,
}


def candidates_to_evidence(field: str, candidates: list[Candidate]) -> list[Evidence]:
    out: list[Evidence] = []
    for c in candidates:
        strategy = c.source.split(".", 1)[0].split(":", 1)[0].split("+", 1)[0]
        if strategy.startswith("json"):
            strategy = "jsonld"
        elif strategy.startswith("og") or strategy.startswith("twitter") or strategy.startswith("article"):
            strategy = "opengraph" if strategy.startswith(("og", "article")) else "meta"
        elif strategy.startswith("semantic") or strategy in {"h1", "title"}:
            strategy = "semantic"
        elif strategy.startswith("heuristic") or strategy == "dom":
            strategy = "dom"
        elif strategy.startswith("meta"):
            strategy = "meta"
        signals: dict[str, Any] = {}
        if isinstance(c.raw, dict):
            signals = {k: v for k, v in c.raw.items() if k != "value"}
        out.append(
            Evidence(
                field=field,
                strategy=strategy,
                value=c.value,
                score=float(c.score),
                source=c.source,
                signals=signals,
            )
        )
    return out


def _normalize_key(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(v).strip().lower() for v in value)
    return str(value).strip().lower()


def _agreement_boost(evidences: list[Evidence], selected: Evidence) -> tuple[float, int]:
    key = _normalize_key(selected.value)
    if not key:
        return 0.0, 0
    agreements = sum(
        1
        for e in evidences
        if e.source != selected.source and _normalize_key(e.value) == key
    )
    # Diminishing boost for agreement across strategies
    boost = min(0.12, 0.04 * agreements)
    return boost, agreements


def _title_penalties(value: str) -> float:
    penalty = 0.0
    words = value.split()
    if len(words) < 3:
        penalty += 0.15
    if len(value) < 12:
        penalty += 0.10
    if _NAV_TITLE_RE.match(value.strip()):
        penalty += 0.35
    if value.isupper() and len(words) > 6:
        penalty += 0.05
    return penalty


def _content_penalties(value: str, signals: dict[str, Any]) -> float:
    penalty = 0.0
    words = len(value.split())
    if words < 40:
        penalty += 0.20
    elif words < 80:
        penalty += 0.08
    link_density = float(signals.get("link_density", 0.0) or 0.0)
    if link_density > 0.35:
        penalty += 0.15
    elif link_density > 0.20:
        penalty += 0.05
    return penalty


def rank_field(
    field: str,
    evidences: list[Evidence],
    *,
    parse_dates: bool = False,
) -> FieldExtraction:
    """Rank evidence for a field and compute confidence."""
    usable: list[Evidence] = []
    for e in evidences:
        if e.value is None:
            continue
        if isinstance(e.value, str) and not e.value.strip():
            continue
        if isinstance(e.value, list) and not e.value:
            continue
        if parse_dates and isinstance(e.value, str) and parse_date(e.value) is None:
            continue
        usable.append(e)

    if not usable:
        return FieldExtraction(candidates=0)

    # Group by normalized value; prefer highest-scoring representative, then boost agreements
    by_value: dict[str, list[Evidence]] = defaultdict(list)
    for e in usable:
        by_value[_normalize_key(e.value)].append(e)

    best: Evidence | None = None
    best_adjusted = float("-inf")
    best_agreements = 0

    for group in by_value.values():
        group.sort(key=lambda e: e.score, reverse=True)
        lead = group[0]
        boost, agreements = _agreement_boost(usable, lead)
        adjusted = lead.score + boost

        if field == "title" and isinstance(lead.value, str):
            adjusted -= _title_penalties(lead.value)
        if field in {"text", "content"} and isinstance(lead.value, str):
            adjusted -= _content_penalties(lead.value, lead.signals)

        if adjusted > best_adjusted:
            best = lead
            best_adjusted = adjusted
            best_agreements = agreements

    assert best is not None
    confidence = max(0.0, min(1.0, best_adjusted))

    return FieldExtraction(
        strategy=best.strategy,
        source=best.source,
        score=round(best.score, 4),
        confidence=round(confidence, 4),
        value=best.value,
        signals=dict(best.signals),
        candidates=len(usable),
        agreements=best_agreements,
    )


def build_confidence(report: ExtractionReport, *, page_type_confidence: float = 0.0) -> Confidence:
    conf = Confidence(
        title=report.title.confidence,
        content=report.content.confidence,
        date=report.date.confidence,
        authors=report.authors.confidence,
        image=report.image.confidence,
        publisher=report.publisher.confidence,
        description=report.description.confidence,
        page_type=round(page_type_confidence, 4),
    )
    # Overall: weighted mean of available fields (skip zeros that were never found)
    total_w = 0.0
    total = 0.0
    for name, weight in _OVERALL_WEIGHTS.items():
        value = getattr(conf, name)
        if value > 0:
            total += value * weight
            total_w += weight
    conf.overall = round(total / total_w, 4) if total_w else 0.0
    return conf


def fuse_title_evidence(evidences: list[Evidence]) -> list[Evidence]:
    """Add synthetic agreement evidence when titles match across strategies."""
    if len(evidences) < 2:
        return evidences
    extra: list[Evidence] = []
    for i, a in enumerate(evidences):
        if not isinstance(a.value, str):
            continue
        for b in evidences[i + 1 :]:
            if not isinstance(b.value, str):
                continue
            if a.value.strip().lower() == b.value.strip().lower() and a.source != b.source:
                extra.append(
                    Evidence(
                        field="title",
                        strategy="fusion",
                        value=a.value.strip(),
                        score=min(1.0, max(a.score, b.score) + 0.05),
                        source=f"{a.source}+{b.source}",
                        signals={"agreement": True},
                    )
                )
    return evidences + extra
