"""Extraction strategies."""

from newsfetch.strategies.base import Candidate
from newsfetch.strategies.heuristic import extract_content_heuristic
from newsfetch.strategies.jsonld import extract_jsonld
from newsfetch.strategies.meta import extract_meta
from newsfetch.strategies.opengraph import extract_opengraph
from newsfetch.strategies.plugin import CallableStrategy, ExtractionStrategy
from newsfetch.strategies.semantic import extract_semantic

__all__ = [
    "CallableStrategy",
    "Candidate",
    "ExtractionStrategy",
    "extract_content_heuristic",
    "extract_jsonld",
    "extract_meta",
    "extract_opengraph",
    "extract_semantic",
]
