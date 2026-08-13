"""Backward-compatible Newspaper façade over the new extraction engine.

Deprecated: prefer ``from newsfetch import fetch`` / ``NewsFetcher``.
"""

from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor

from newsfetch.api import NewsFetcher
from newsfetch.normalize.url import domain_from_url


class Newspaper:
    """Legacy API mirroring news-fetch ≤0.4.

    .. deprecated:: 0.5
       Use :func:`newsfetch.fetch` or :class:`newsfetch.NewsFetcher` instead.
    """

    def __init__(self, url: str) -> None:
        warnings.warn(
            "newsfetch.news.Newspaper is deprecated; use newsfetch.fetch() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.url = url
        article = NewsFetcher().fetch(url)
        self.headline = article.title
        self.article = article.text
        self.authors = article.authors
        self.date_publish = article.published_at.isoformat() if article.published_at else None
        self.date_modify = article.modified_at.isoformat() if article.modified_at else None
        self.image_url = article.image
        self.language = article.language
        self.publication = article.publisher
        self.category = article.section
        self.keywords = article.keywords
        self.summary = article.summary
        self.source_domain = domain_from_url(article.canonical_url or article.url)
        self.source_favicon_url = None
        self.description = article.description or article.summary
        self.word_count = article.word_count
        self.reading_time_minutes = article.reading_time_minutes
        self.get_dict = {
            "headline": self.headline,
            "author": self.authors,
            "date_publish": self.date_publish,
            "date_modify": self.date_modify,
            "language": self.language,
            "image_url": self.image_url,
            "description": self.description,
            "publication": self.publication,
            "category": self.category,
            "source_domain": self.source_domain,
            "source_favicon_url": self.source_favicon_url,
            "article": self.article,
            "summary": self.summary,
            "keyword": self.keywords,
            "word_count": self.word_count,
            "reading_time_minutes": self.reading_time_minutes,
            "url": self.url,
        }

    @classmethod
    def from_urls(cls, urls: list[str], max_workers: int = 5) -> list[Newspaper | None]:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(cls.__safe_init, urls))

    @classmethod
    def __safe_init(cls, url: str) -> Newspaper | None:
        try:
            result = cls(url=url)
        except Exception:
            return None
        return result if (result.headline or result.article) else None
