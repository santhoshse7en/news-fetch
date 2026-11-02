"""Article and related models."""

from newsfetch.models.article import Article, CandidateTrace, ExtractionTrace, FieldSource
from newsfetch.models.evidence import Confidence, Evidence, ExtractionReport, FieldExtraction
from newsfetch.models.result import FetchResult

__all__ = [
    "Article",
    "CandidateTrace",
    "Confidence",
    "Evidence",
    "ExtractionReport",
    "ExtractionTrace",
    "FetchResult",
    "FieldExtraction",
    "FieldSource",
]
