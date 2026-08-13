"""Shared extraction candidate type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Candidate(Generic[T]):
    """A scored extraction candidate for a field."""

    value: T
    source: str
    score: float
    raw: Any = None
