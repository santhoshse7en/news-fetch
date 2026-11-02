"""Language detection from document signals."""

from __future__ import annotations

import re

from newsfetch.parser.html import Document

# BCP 47 primary language subtag: 2–3 letters (ISO 639), or 4–8 for registered tags
_PRIMARY_SUBTAG_RE = re.compile(r"^[a-z]{2,8}$")


def normalize_language(value: str | None) -> str | None:
    """Reduce a language tag (``en-GB``, ``pt_BR``, ``fil``, ``en, fr``) to its primary subtag."""
    if not value:
        return None
    primary = value.split(",", 1)[0].strip().replace("_", "-").split("-", 1)[0].lower()
    return primary if _PRIMARY_SUBTAG_RE.match(primary) else None


def detect_language(doc: Document, fallback: str | None = None) -> str | None:
    for lang in doc.xpath("//html/@lang"):
        normalized = normalize_language(str(lang))
        if normalized:
            return normalized
    return normalize_language(doc.meta_content(property="og:locale")) or fallback
