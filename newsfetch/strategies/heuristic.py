"""DOM gravity / content scoring for article body extraction."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

from lxml.html import HtmlElement

from newsfetch.normalize.text import normalize_whitespace
from newsfetch.parser.html import Document
from newsfetch.strategies.base import Candidate

# Compact English stopword list for density scoring (not NLP quality)
_STOPWORDS = {
    "a", "about", "after", "all", "also", "an", "and", "any", "as", "at", "be",
    "because", "been", "before", "being", "between", "both", "but", "by", "can",
    "could", "did", "do", "does", "during", "each", "for", "from", "had", "has",
    "have", "he", "her", "him", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "just", "like", "made", "may", "more", "most", "new", "no", "not", "now",
    "of", "on", "one", "only", "or", "other", "our", "out", "over", "said", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "will", "with", "would", "you", "your",
}

_NEGATIVE_RE = re.compile(
    r"comment|footer|header|menu|nav|sidebar|related|promo|share|social|"
    r"newsletter|subscribe|advert|cookie|breadcrumb|pagination|popup|modal",
    re.I,
)
_POSITIVE_RE = re.compile(
    r"article|story|content|entry|post|text|body|paragraph|main",
    re.I,
)


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def _stopword_count(text: str) -> int:
    return sum(1 for w in _words(text) if w in _STOPWORDS)


def _direct_text(node: HtmlElement) -> str:
    parts: list[str] = []
    if node.text:
        parts.append(node.text)
    for child in node:
        if child.tail:
            parts.append(child.tail)
    return " ".join(parts)


def _link_density(node: HtmlElement) -> float:
    text = " ".join(t.strip() for t in node.itertext() if t and t.strip())
    words = max(len(_words(text)), 1)
    link_words = 0
    for a in node.xpath(".//a"):
        link_words += len(_words(" ".join(a.itertext())))
    return link_words / words


def _class_id(node: HtmlElement) -> str:
    return f"{node.get('class', '')} {node.get('id', '')}"


def _is_unlikely(node: HtmlElement) -> bool:
    token = _class_id(node)
    if _POSITIVE_RE.search(token):
        return False
    return bool(_NEGATIVE_RE.search(token))


def _paragraphs_from(node: HtmlElement) -> str:
    paras: list[str] = []
    for p in node.xpath(".//p|.//li|.//h2|.//h3"):
        text = " ".join(t.strip() for t in p.itertext() if t and t.strip()).strip()
        if len(text) >= 20 and _link_density(p) < 0.5:
            paras.append(text)
    if paras:
        return normalize_whitespace("\n\n".join(paras))
    text = " ".join(t.strip() for t in node.itertext() if t and t.strip())
    return normalize_whitespace(text)


def _candidates(root: HtmlElement) -> list[HtmlElement]:
    tags = ("p", "pre", "td", "article", "section", "div")
    nodes: list[HtmlElement] = []
    for tag in tags:
        for node in root.iter(tag):
            if tag in {"div", "section"}:
                token = _class_id(node)
                if not (_POSITIVE_RE.search(token) or node.get("itemprop") == "articleBody"):
                    # Keep divs with several paragraph children
                    if len(node.xpath("./p")) < 2:
                        continue
            if _is_unlikely(node):
                continue
            nodes.append(node)
    return nodes


def extract_content_heuristic(doc: Document) -> list[Candidate[str]]:
    """Score DOM regions and return the best article-body candidate(s)."""
    root = doc.root
    scored: dict[HtmlElement, float] = {}

    # Semantic boosts
    for sel, boost in (
        ('[itemprop="articleBody"]', 100.0),
        ("article", 25.0),
        ('[role="main"]', 15.0),
        ("main", 12.0),
    ):
        for node in doc.css(sel)[:5]:
            scored[node] = scored.get(node, 0.0) + boost

    nodes = _candidates(root)
    for node in nodes:
        text = _direct_text(node)
        if not text.strip():
            # Use shallow text mass for leaf-ish paragraphs
            text = " ".join(t.strip() for t in node.itertext() if t and t.strip())[:2000]
        sw = _stopword_count(text)
        wc = len(_words(text))
        if sw < 2 and wc < 15:
            continue
        density = _link_density(node)
        if density > 0.45 and wc < 80:
            continue

        score = float(sw) + math.log1p(wc)
        token = _class_id(node)
        if _POSITIVE_RE.search(token):
            score += 15
        if node.tag == "p":
            score += 5

        parent = node.getparent()
        if parent is not None:
            scored[parent] = scored.get(parent, 0.0) + score
            grand = parent.getparent()
            if grand is not None:
                scored[grand] = scored.get(grand, 0.0) + score * 0.4

    if not scored:
        return []

    # Prefer highest score with enough text
    ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    results: list[Candidate[str]] = []
    for node, score in ranked[:5]:
        text = _paragraphs_from(node)
        if len(text) < 80:
            continue
        # Normalize score into 0.4–0.9 band for merging with other strategies
        norm = min(0.9, 0.45 + (score / 200.0))
        results.append(Candidate(text, "heuristic.dom-score", norm, raw={"score": score}))
        break  # best only as primary; keep one strong candidate

    return results


def strip_boilerplate_nodes(root: HtmlElement) -> None:
    """Remove obvious non-content tags in-place before scoring (safe subset)."""
    for tag in ("script", "style", "noscript", "svg", "iframe", "form"):
        for node in list(root.iter(tag)):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
    for node in list(root.iter("nav", "aside", "footer", "header")):
        # Keep header if it might contain the only h1 — only strip nav/aside/footer aggressively
        if node.tag in {"nav", "aside", "footer"}:
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)


def iter_images_near(node: HtmlElement) -> Iterable[str]:
    for img in node.xpath(".//img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src and not src.startswith("data:"):
            yield src
        srcset = img.get("srcset")
        if srcset:
            first = srcset.split(",")[0].strip().split(" ")[0]
            if first and not first.startswith("data:"):
                yield first
