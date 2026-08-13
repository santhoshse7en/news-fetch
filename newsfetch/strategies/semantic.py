"""Semantic HTML extraction (article, time, h1, bylines)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate

_BYLINE_RE = re.compile(r"by\s+(.+)", re.I)
_AUTHOR_STOP = {
    "by",
    "reuters",
    "associated press",
    "ap",
    "afp",
    "pti",
    "ians",
    "ani",
    "staff",
    "reporter",
    "editor",
}


def _node_text(node: HtmlElement) -> str:
    return " ".join(t.strip() for t in node.itertext() if t and t.strip()).strip()


def extract_semantic(doc: Document) -> dict[str, list[Candidate]]:
    out: dict[str, list[Candidate]] = {
        "title": [],
        "published_at": [],
        "modified_at": [],
        "authors": [],
        "text": [],
        "image": [],
    }

    # h1
    for h1 in doc.css("h1")[:3]:
        text = _node_text(h1)
        if len(text.split()) >= 2:
            out["title"].append(Candidate(text, "semantic.h1", 0.72))
            break

    # <title>
    title_nodes = doc.css("title")
    if title_nodes:
        raw = _node_text(title_nodes[0])
        if raw:
            # Split common site-name separators
            piece = raw
            for sep in (" | ", " - ", " — ", " · ", " :: ", " » "):
                if sep in raw:
                    parts = [p.strip() for p in raw.split(sep) if p.strip()]
                    if parts:
                        piece = max(parts, key=len)
                    break
            out["title"].append(Candidate(piece, "semantic.title", 0.55))

    # <time datetime>
    for time_el in doc.css("time[datetime]")[:10]:
        dt = time_el.get("datetime")
        if not dt:
            continue
        label = (_node_text(time_el) + " " + " ".join(time_el.get("class", "").split())).lower()
        if "modif" in label or "updated" in label:
            out["modified_at"].append(Candidate(dt, "semantic.time.modified", 0.75))
        else:
            score = 0.8 if "publish" in label else 0.72
            out["published_at"].append(Candidate(dt, "semantic.time", score))

    # itemprop=datePublished
    for node in doc.css('[itemprop="datePublished"]')[:5]:
        dt = node.get("content") or node.get("datetime") or _node_text(node)
        if dt:
            out["published_at"].append(Candidate(dt, "semantic.itemprop.datePublished", 0.85))

    for node in doc.css('[itemprop="dateModified"]')[:5]:
        dt = node.get("content") or node.get("datetime") or _node_text(node)
        if dt:
            out["modified_at"].append(Candidate(dt, "semantic.itemprop.dateModified", 0.8))

    # authors via itemprop / rel / class byline
    authors: list[str] = []
    for sel in (
        '[itemprop="author"] [itemprop="name"]',
        '[itemprop="author"]',
        'a[rel="author"]',
        ".byline",
        ".author",
        ".c-byline",
    ):
        for node in doc.css(sel)[:5]:
            text = _node_text(node)
            if not text:
                continue
            match = _BYLINE_RE.match(text)
            text = match.group(1) if match else text
            for part in re.split(r"\s*(?:,| and | & |/)\s*", text):
                part = part.strip(" .")
                if 2 <= len(part.split()) <= 5 and part.lower() not in _AUTHOR_STOP:
                    authors.append(part)
        if authors:
            break
    if authors:
        seen: set[str] = set()
        uniq = []
        for a in authors:
            key = a.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(a)
        out["authors"].append(Candidate(uniq, "semantic.byline", 0.7))

    # itemprop=articleBody
    for node in doc.css('[itemprop="articleBody"]')[:2]:
        text = _paragraphs_text(node)
        if len(text) > 80:
            out["text"].append(Candidate(text, "semantic.itemprop.articleBody", 0.92))

    for node in doc.css("article")[:3]:
        text = _paragraphs_text(node)
        if len(text) > 120:
            out["text"].append(Candidate(text, "semantic.article", 0.78))

    # lead image inside article
    for node in doc.css("article img[src], figure img[src]")[:5]:
        src = node.get("src") or node.get("data-src")
        if src and not src.startswith("data:"):
            out["image"].append(Candidate(src, "semantic.img", 0.55))
            break

    return out


def _paragraphs_text(node: HtmlElement) -> str:
    parts: list[str] = []
    for p in node.xpath(".//p"):
        text = _node_text(p)
        if len(text) >= 25:
            parts.append(text)
    if parts:
        return "\n\n".join(parts)
    return _node_text(node)
