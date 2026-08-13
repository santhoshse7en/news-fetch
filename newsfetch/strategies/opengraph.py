"""Open Graph and Twitter Card extraction."""

from __future__ import annotations

from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate

_OG_MAP = {
    "title": ("og:title", 0.85),
    "description": ("og:description", 0.8),
    "image": ("og:image", 0.88),
    "canonical_url": ("og:url", 0.8),
    "publisher": ("og:site_name", 0.75),
    "section": ("article:section", 0.7),
    "published_at": ("article:published_time", 0.88),
    "modified_at": ("article:modified_time", 0.8),
}

_TWITTER_MAP = {
    "title": ("twitter:title", 0.7),
    "description": ("twitter:description", 0.65),
    "image": ("twitter:image", 0.7),
}


def extract_opengraph(doc: Document) -> dict[str, list[Candidate]]:
    keys = set(_OG_MAP) | set(_TWITTER_MAP) | {"authors", "language"}
    out: dict[str, list[Candidate]] = {k: [] for k in keys}

    for field, (prop, score) in _OG_MAP.items():
        value = doc.meta_content(property=prop)
        if value:
            out[field].append(Candidate(value, prop, score))

    # article:author may be URL or name
    author = doc.meta_content(property="article:author")
    if author and not author.startswith("http"):
        out["authors"].append(Candidate([author], "article:author", 0.7))

    locale = doc.meta_content(property="og:locale")
    if locale:
        out["language"].append(Candidate(locale.replace("_", "-")[:2].lower(), "og:locale", 0.65))

    for field, (name, score) in _TWITTER_MAP.items():
        value = doc.meta_content(name=name)
        if value:
            out[field].append(Candidate(value, name, score))

    return out
