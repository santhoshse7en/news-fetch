"""JSON-LD / schema.org extraction."""

from __future__ import annotations

import json
import re
from typing import Any

from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate

_ARTICLE_TYPES = {
    "article",
    "newsarticle",
    "reportagenewsarticle",
    "blogposting",
    "scholarlyarticle",
    "techarticle",
    "webpage",
}


def _types_of(obj: dict) -> set[str]:
    raw = obj.get("@type", "")
    if isinstance(raw, list):
        return {str(t).lower() for t in raw}
    return {str(raw).lower()} if raw else set()


def _is_article(obj: dict) -> bool:
    types = _types_of(obj)
    return bool(types & _ARTICLE_TYPES) or any("article" in t for t in types)


def _walk(node: Any) -> list[dict]:
    found: list[dict] = []
    if isinstance(node, dict):
        if "@graph" in node and isinstance(node["@graph"], list):
            for item in node["@graph"]:
                found.extend(_walk(item))
        else:
            found.append(node)
            for value in node.values():
                if isinstance(value, (dict, list)):
                    found.extend(_walk(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk(item))
    return found


def _load_blocks(doc: Document) -> list[dict]:
    blocks: list[dict] = []
    for script in doc.css('script[type="application/ld+json"]'):
        text = (script.text or "").strip()
        if not text:
            continue
        # Some sites concatenate multiple JSON objects; try repair lightly
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        for obj in _walk(data):
            if isinstance(obj, dict):
                blocks.append(obj)
    return blocks


def article_objects(doc: Document) -> list[dict]:
    objs = [o for o in _load_blocks(doc) if _is_article(o)]
    if objs:
        return objs
    # Fallback: any object with headline/articleBody
    return [
        o
        for o in _load_blocks(doc)
        if isinstance(o, dict) and (o.get("headline") or o.get("articleBody") or o.get("name"))
    ]


def _author_names(author: Any) -> list[str]:
    names: list[str] = []
    if isinstance(author, list):
        for item in author:
            names.extend(_author_names(item))
    elif isinstance(author, dict):
        name = author.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    elif isinstance(author, str) and author.strip():
        names.append(author.strip())
    return names


def _publisher_name(publisher: Any) -> str | None:
    if isinstance(publisher, dict):
        name = publisher.get("name")
        return name.strip() if isinstance(name, str) and name.strip() else None
    if isinstance(publisher, str) and publisher.strip():
        return publisher.strip()
    return None


def extract_jsonld(doc: Document) -> dict[str, list[Candidate]]:
    """Return field → candidates from JSON-LD article objects."""
    out: dict[str, list[Candidate]] = {
        "title": [],
        "description": [],
        "authors": [],
        "published_at": [],
        "modified_at": [],
        "publisher": [],
        "image": [],
        "text": [],
        "section": [],
        "language": [],
        "canonical_url": [],
        "keywords": [],
    }

    for obj in article_objects(doc):
        title = obj.get("headline") or obj.get("name")
        if isinstance(title, str) and title.strip():
            out["title"].append(Candidate(title.strip(), "json-ld", 0.95))

        desc = obj.get("description")
        if isinstance(desc, str) and desc.strip():
            out["description"].append(Candidate(desc.strip(), "json-ld", 0.9))

        authors = _author_names(obj.get("author"))
        if authors:
            out["authors"].append(Candidate(authors, "json-ld", 0.95))

        for key, field, score in (
            ("datePublished", "published_at", 0.95),
            ("dateCreated", "published_at", 0.75),
            ("dateModified", "modified_at", 0.9),
        ):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                out[field].append(Candidate(value.strip(), f"json-ld.{key}", score))

        pub = _publisher_name(obj.get("publisher"))
        if pub:
            out["publisher"].append(Candidate(pub, "json-ld", 0.9))

        body = obj.get("articleBody")
        if isinstance(body, str) and len(body.strip()) > 40:
            out["text"].append(Candidate(body.strip(), "json-ld.articleBody", 0.98))

        section = obj.get("articleSection")
        if isinstance(section, str) and section.strip():
            out["section"].append(Candidate(section.strip(), "json-ld", 0.85))
        elif isinstance(section, list):
            joined = ", ".join(str(s) for s in section if s)
            if joined:
                out["section"].append(Candidate(joined, "json-ld", 0.85))

        lang = obj.get("inLanguage")
        if isinstance(lang, str) and lang.strip():
            out["language"].append(Candidate(lang.strip()[:2].lower(), "json-ld", 0.8))

        url = obj.get("mainEntityOfPage") or obj.get("url")
        if isinstance(url, dict):
            url = url.get("@id") or url.get("url")
        if isinstance(url, str) and url.startswith("http"):
            out["canonical_url"].append(Candidate(url, "json-ld", 0.85))

        image = obj.get("image")
        image_url = None
        if isinstance(image, str):
            image_url = image
        elif isinstance(image, list) and image:
            first = image[0]
            if isinstance(first, str):
                image_url = first
            elif isinstance(first, dict):
                image_url = first.get("url")
            else:
                image_url = None
        elif isinstance(image, dict):
            image_url = image.get("url")
        if isinstance(image_url, str) and image_url.strip():
            out["image"].append(Candidate(image_url.strip(), "json-ld", 0.9))

        keywords = obj.get("keywords")
        if isinstance(keywords, str):
            parts = [k.strip() for k in re.split(r"[,;]", keywords) if k.strip()]
            if parts:
                out["keywords"].append(Candidate(parts, "json-ld", 0.7))
        elif isinstance(keywords, list):
            parts = [str(k).strip() for k in keywords if str(k).strip()]
            if parts:
                out["keywords"].append(Candidate(parts, "json-ld", 0.7))

    return out
