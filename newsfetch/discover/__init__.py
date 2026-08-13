"""Site-wide article URL discovery via sitemaps and RSS/Atom."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from lxml import etree

_SITEMAP_FALLBACKS = ("/sitemap.xml", "/sitemap_news.xml", "/news-sitemap.xml", "/sitemap-news.xml")
_MAX_FEEDS = 8
_MAX_SITEMAP_DEPTH = 1
_TIMEOUT = 10
_FEED_TYPE_RE = re.compile(r"rss|atom|xml", re.I)


class DiscoveredArticle:
    __slots__ = ("url", "title", "date")

    def __init__(self, url: str, title: str | None = None, date: str | None = None) -> None:
        self.url = url
        self.title = title
        self.date = date

    def to_dict(self) -> dict:
        return {"url": self.url, "title": self.title, "date": self.date}


def discover(news_domain: str, *, limit: int | None = 50, timeout: float = _TIMEOUT) -> list[dict]:
    """Discover recent article URLs for a news site.

    Uses robots.txt Sitemap directives, homepage feed autodiscovery, and common
    sitemap paths — not a search engine.
    """
    extractor = SiteDiscoverer(news_domain, limit=limit, timeout=timeout)
    return [a.to_dict() for a in extractor.articles]


class SiteDiscoverer:
    """Discover article URLs from sitemaps and feeds."""

    def __init__(
        self,
        news_domain: str,
        *,
        limit: int | None = 50,
        timeout: float = _TIMEOUT,
    ) -> None:
        self.news_domain = news_domain.rstrip("/")
        self.timeout = timeout
        self.articles: list[DiscoveredArticle] = self._discover(limit)
        self.urls: list[str] = [a.url for a in self.articles]

    def _get(self, url: str) -> requests.Response | None:
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp
        except Exception:
            return None

    def _discover(self, limit: int | None) -> list[DiscoveredArticle]:
        found: dict[str, DiscoveredArticle] = {}
        for feed_url in self._candidate_feed_urls():
            for article in self._parse_feed(feed_url, depth=0):
                found.setdefault(article.url, article)
        results = list(found.values())
        return results if limit is None else results[:limit]

    def _candidate_feed_urls(self) -> list[str]:
        candidates: list[str] = []

        robots = self._get(f"{self.news_domain}/robots.txt")
        if robots is not None:
            for line in robots.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    candidates.append(line.split(":", 1)[1].strip())

        homepage = self._get(self.news_domain)
        if homepage is not None:
            try:
                root = etree.HTML(homepage.content)
            except Exception:
                root = None
            if root is not None:
                for link in root.xpath("//link[@href]"):
                    type_ = (link.get("type") or "") + " " + (link.get("rel") or "")
                    if _FEED_TYPE_RE.search(type_):
                        href = link.get("href")
                        if href:
                            candidates.append(urljoin(self.news_domain, href))

        if not candidates:
            candidates = [self.news_domain + path for path in _SITEMAP_FALLBACKS]

        seen: set[str] = set()
        deduped: list[str] = []
        for url in candidates:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        deduped.sort(key=lambda u: "news" not in u.lower())
        return deduped[:_MAX_FEEDS]

    def _parse_feed(self, feed_url: str, depth: int) -> list[DiscoveredArticle]:
        if depth > _MAX_SITEMAP_DEPTH:
            return []
        response = self._get(feed_url)
        if response is None:
            return []
        try:
            root = etree.fromstring(response.content)
        except Exception:
            try:
                root = etree.HTML(response.content)
            except Exception:
                return []

        # Strip namespaces for simpler queries
        for elem in root.iter():
            if isinstance(elem.tag, str) and "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        tag = root.tag.lower() if isinstance(root.tag, str) else ""
        if root.find(".//sitemapindex") is not None or tag == "sitemapindex":
            articles: list[DiscoveredArticle] = []
            for loc in root.findall(".//loc"):
                text = (loc.text or "").strip()
                if text and "news" in text.lower():
                    articles.extend(self._parse_feed(text, depth=depth + 1))
            return articles

        if root.find(".//urlset") is not None or tag == "urlset":
            results = []
            for url_tag in root.findall(".//url"):
                entry = self._entry_from_url(url_tag)
                if entry:
                    results.append(entry)
            return results

        if (
            root.find(".//rss") is not None
            or tag == "rss"
            or root.find(".//feed") is not None
            or tag == "feed"
        ):
            results = []
            for item in root.findall(".//item") + root.findall(".//entry"):
                entry = self._entry_from_item(item)
                if entry:
                    results.append(entry)
            return results

        return []

    @staticmethod
    def _entry_from_url(tag) -> DiscoveredArticle | None:
        loc = tag.find("loc")
        url = (loc.text or "").strip() if loc is not None else ""
        if not url:
            return None
        title_tag = tag.find(".//title")
        date = None
        for key in ("publication_date", "lastmod"):
            node = tag.find(f".//{key}")
            if node is not None and (node.text or "").strip():
                date = node.text.strip()
                break
        title = title_tag.text.strip() if title_tag is not None and title_tag.text else None
        return DiscoveredArticle(url=url, title=title, date=date)

    @staticmethod
    def _entry_from_item(tag) -> DiscoveredArticle | None:
        link = tag.find("link")
        url = None
        if link is not None:
            url = (link.get("href") or (link.text or "")).strip() or None
        if not url:
            return None
        title_tag = tag.find("title")
        date = None
        for key in ("pubDate", "published", "updated"):
            node = tag.find(key)
            if node is not None and (node.text or "").strip():
                date = node.text.strip()
                break
        title = title_tag.text.strip() if title_tag is not None and title_tag.text else None
        return DiscoveredArticle(url=url, title=title, date=date)


# Back-compat alias used by older news-fetch code
class NewsSiteURLExtractor(SiteDiscoverer):
    def __init__(self, news_domain: str, limit: int | None = 50) -> None:
        super().__init__(news_domain, limit=limit)
        # Old API exposed list[dict]
        self.articles = [a.to_dict() for a in self.articles]  # type: ignore[assignment]
