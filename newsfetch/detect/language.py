"""Language detection from document signals."""

from __future__ import annotations

from newsfetch.parser.html import Document


def detect_language(doc: Document, fallback: str | None = None) -> str | None:
    lang = doc.xpath("string(//html/@lang)")
    if isinstance(lang, str) and lang.strip():
        return lang.strip().replace("_", "-")[:2].lower()
    content = doc.meta_content(property="og:locale")
    if content:
        return content.replace("_", "-")[:2].lower()
    return fallback
