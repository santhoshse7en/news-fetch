"""news-fetch — lightweight, independent, explainable news extraction for Python."""

from newsfetch.api import NewsFetcher, discover, extract, fetch, fetch_iter, fetch_many
from newsfetch.async_api import fetch_async, fetch_many_async
from newsfetch.config import Config
from newsfetch.errors import (
    DiscoveryError,
    ExtractionError,
    FetchError,
    LowConfidenceExtractionError,
    NewsFetchError,
    ParseError,
)
from newsfetch.models import Article, Confidence, Evidence, ExtractionReport, FieldExtraction
from newsfetch.strategies.plugin import CallableStrategy, ExtractionStrategy

__version__ = "1.0.0"

__all__ = [
    "Article",
    "CallableStrategy",
    "Confidence",
    "Config",
    "DiscoveryError",
    "Evidence",
    "ExtractionError",
    "ExtractionReport",
    "ExtractionStrategy",
    "FetchError",
    "FieldExtraction",
    "LowConfidenceExtractionError",
    "NewsFetchError",
    "NewsFetcher",
    "ParseError",
    "__version__",
    "discover",
    "extract",
    "fetch",
    "fetch_async",
    "fetch_iter",
    "fetch_many",
    "fetch_many_async",
]
