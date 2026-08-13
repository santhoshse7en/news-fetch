"""Generic HTML meta and semantic tag extraction."""

from __future__ import annotations

from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate

_META_TITLE = ("parsely-title", "sailthru.title", "title", "dc.title", "DC.title")
_META_DESC = ("description", "sailthru.description", "dc.description")
_META_PUBLISHED = (
    "article:published_time",
    "pubdate",
    "publishdate",
    "date",
    "dc.date",
    "DC.date",
    "dc.date.issued",
    "sailthru.date",
    "parsely-pub-date",
    "datePublished",
    "publication_date",
)
_META_MODIFIED = (
    "article:modified_time",
    "last-modified",
    "datemodified",
    "og:updated_time",
)
_META_AUTHOR = ("author", "dc.creator", "DC.creator", "byl", "sailthru.author", "parsely-author")
_META_SECTION = ("article:section", "section", "category")
_META_KEYWORDS = ("keywords", "news_keywords", "sailthru.tags")


def extract_meta(doc: Document) -> dict[str, list[Candidate]]:
    out: dict[str, list[Candidate]] = {
        "title": [],
        "description": [],
        "published_at": [],
        "modified_at": [],
        "authors": [],
        "section": [],
        "keywords": [],
        "language": [],
        "canonical_url": [],
        "publisher": [],
        "image": [],
    }

    for name in _META_TITLE:
        value = doc.meta_content(name=name)
        if value:
            out["title"].append(Candidate(value, f"meta[name={name}]", 0.6))

    for name in _META_DESC:
        value = doc.meta_content(name=name)
        if value:
            out["description"].append(Candidate(value, f"meta[name={name}]", 0.7))

    for name in _META_PUBLISHED:
        value = doc.meta_content(name=name) or doc.meta_content(property=name)
        if value:
            out["published_at"].append(Candidate(value, f"meta:{name}", 0.7))

    for name in _META_MODIFIED:
        value = doc.meta_content(name=name) or doc.meta_content(property=name)
        if value:
            out["modified_at"].append(Candidate(value, f"meta:{name}", 0.65))

    authors: list[str] = []
    for name in _META_AUTHOR:
        value = doc.meta_content(name=name) or doc.meta_content(property=name)
        if value and not value.startswith("http"):
            authors.append(value)
    if authors:
        seen: set[str] = set()
        uniq: list[str] = []
        for author in authors:
            key = author.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(author)
        out["authors"].append(Candidate(uniq, "meta.author", 0.65))

    for name in _META_SECTION:
        value = doc.meta_content(name=name) or doc.meta_content(property=name)
        if value:
            out["section"].append(Candidate(value, f"meta:{name}", 0.6))

    for name in _META_KEYWORDS:
        value = doc.meta_content(name=name)
        if value:
            parts = [p.strip() for p in value.split(",") if p.strip()]
            if parts:
                out["keywords"].append(Candidate(parts, f"meta:{name}", 0.55))

    lang_attr = doc.xpath("string(//html/@lang)")
    if isinstance(lang_attr, str) and lang_attr.strip():
        out["language"].append(Candidate(lang_attr.strip()[:2].lower(), "html[lang]", 0.75))

    for node in doc.css('meta[http-equiv="content-language"]'):
        content = node.get("content")
        if content:
            out["language"].append(
                Candidate(content.strip()[:2].lower(), "meta.content-language", 0.7)
            )
            break

    for node in doc.css('link[rel="canonical"]'):
        href = node.get("href")
        if href:
            out["canonical_url"].append(Candidate(href.strip(), "link[rel=canonical]", 0.9))
            break

    app = doc.meta_content(name="application-name") or doc.meta_content(name="publisher")
    if app:
        out["publisher"].append(Candidate(app, "meta.publisher", 0.5))

    return out
