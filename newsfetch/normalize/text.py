"""Text normalization helpers."""

from __future__ import annotations

import re

_WS_RE = re.compile(r"[ \t\x0b\f\r]+")
_BLANK_RE = re.compile(r"\n{3,}")


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces and limit blank lines."""
    text = text.replace("\xa0", " ")
    text = _WS_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = _BLANK_RE.sub("\n\n", text)
    return text.strip()


def collapse_to_single_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
