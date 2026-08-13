"""Page-type classification for news URLs / documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from newsfetch.parser.html import Document

_HOMEPAGE_RE = re.compile(r"^https?://[^/]+/?$", re.I)
_CATEGORY_RE = re.compile(
    r"/(category|categories|section|sections|topic|topics|tag|tags|author|authors)(/|$)",
    re.I,
)
_SEARCH_RE = re.compile(r"/(search|find)(/|$)|[?&](q|query|s)=", re.I)
_LIVE_RE = re.compile(r"/live(/|$)|live[-_ ]?blog|live[-_ ]?news", re.I)
_VIDEO_RE = re.compile(r"/(video|videos|watch)(/|$)", re.I)
_GALLERY_RE = re.compile(r"/(gallery|photos|slideshow)(/|$)", re.I)
_OPINION_RE = re.compile(r"/(opinion|opinions|commentisfree|editorial)(/|$)", re.I)
_REVIEW_RE = re.compile(r"/(review|reviews)(/|$)", re.I)
_ARTICLE_HINT_RE = re.compile(
    r"/(news|story|article|articles|world|politics|business|sport|sports)/\S+",
    re.I,
)


@dataclass(frozen=True)
class PageTypeResult:
    page_type: str
    confidence: float
    is_article: bool
    reasons: tuple[str, ...] = ()


def detect_page_type(doc: Document, url: str, *, has_article_body: bool = False) -> PageTypeResult:
    """Classify whether a page looks like a news article vs listing/chrome."""
    reasons: list[str] = []
    scores: dict[str, float] = {
        "article": 0.15,
        "homepage": 0.0,
        "category": 0.0,
        "search": 0.0,
        "live_blog": 0.0,
        "video": 0.0,
        "gallery": 0.0,
        "opinion": 0.0,
        "review": 0.0,
        "unknown": 0.05,
    }

    if _HOMEPAGE_RE.match(url.strip()):
        scores["homepage"] += 0.7
        reasons.append("url.homepage")
    if _CATEGORY_RE.search(url):
        scores["category"] += 0.55
        reasons.append("url.category")
    if _SEARCH_RE.search(url):
        scores["search"] += 0.7
        reasons.append("url.search")
    if _LIVE_RE.search(url):
        scores["live_blog"] += 0.6
        reasons.append("url.live")
    if _VIDEO_RE.search(url):
        scores["video"] += 0.5
        reasons.append("url.video")
    if _GALLERY_RE.search(url):
        scores["gallery"] += 0.5
        reasons.append("url.gallery")
    if _OPINION_RE.search(url):
        scores["opinion"] += 0.55
        reasons.append("url.opinion")
    if _REVIEW_RE.search(url):
        scores["review"] += 0.5
        reasons.append("url.review")
    if _ARTICLE_HINT_RE.search(url):
        scores["article"] += 0.25
        reasons.append("url.article_path")

    # DOM signals
    articles = doc.css("article")
    if articles:
        scores["article"] += 0.2
        reasons.append("dom.article")
    if doc.css('[itemprop="articleBody"], [itemtype*="NewsArticle"], [itemtype*="Article"]'):
        scores["article"] += 0.35
        reasons.append("dom.schema_article")
    if has_article_body:
        scores["article"] += 0.25
        reasons.append("extract.body")

    # Many nav-like links and few paragraphs → listing
    paragraphs = doc.css("p")
    links = doc.css("a")
    if len(links) > 80 and len(paragraphs) < 5:
        scores["category"] += 0.25
        scores["homepage"] += 0.15
        scores["article"] -= 0.2
        reasons.append("dom.link_heavy")

    og_type = (doc.meta_content(property="og:type") or "").lower()
    if "article" in og_type:
        scores["article"] += 0.3
        reasons.append("og:type=article")
    if og_type in {"website", "profile"}:
        scores["homepage"] += 0.2

    page_type = max(scores, key=scores.get)
    confidence = max(0.0, min(1.0, scores[page_type]))
    is_article = page_type in {"article", "opinion", "review", "live_blog"} and confidence >= 0.35
    if page_type == "unknown" and has_article_body:
        page_type = "article"
        is_article = True
        confidence = max(confidence, 0.55)
        reasons.append("fallback.body")

    return PageTypeResult(
        page_type=page_type,
        confidence=round(confidence, 4),
        is_article=is_article,
        reasons=tuple(reasons),
    )
