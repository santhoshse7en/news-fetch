"""Strategy plugin protocol for the extraction engine."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate


@runtime_checkable
class ExtractionStrategy(Protocol):
    """Produce field → candidate evidence from a parsed document."""

    name: str

    def extract(self, document: Document) -> dict[str, list[Candidate]]:
        ...


class CallableStrategy:
    """Wrap a plain function as an ExtractionStrategy."""

    def __init__(self, name: str, func) -> None:
        self.name = name
        self._func = func

    def extract(self, document: Document) -> dict[str, list[Candidate]]:
        return self._func(document)
