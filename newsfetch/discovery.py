import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

_SITEMAP_FALLBACKS = ["/sitemap.xml", "/sitemap_news.xml", "/news-sitemap.xml", "/sitemap-news.xml"]
_MAX_FEEDS = 8
_MAX_SITEMAP_DEPTH = 1
_TIMEOUT = 10


class NewsSiteURLExtractor:
    """Discover recent article URLs for a news site via its sitemaps and RSS/Atom feeds.

    Uses the same discovery mechanisms real news aggregators rely on (robots.txt
    'Sitemap:' directives, Google News sitemaps, RSS/Atom autodiscovery) instead
    of scraping a search engine, so no browser automation is needed.
    """

    def __init__(self, news_domain: str, limit: int | None = 50) -> None:
        """Initialize with the news site's homepage URL and a result limit."""
        self.news_domain = news_domain.rstrip("/")
        self.articles: list[dict] = self.__discover(limit)
        self.urls: list[str] = [article["url"] for article in self.articles]

    def __discover(self, limit: int | None) -> list[dict]:
        """Fetch every candidate feed, merge results, and de-duplicate by URL."""
        articles = {}
        for feed_url in self.__candidate_feed_urls():
            for article in self.__parse_feed(feed_url, depth=0):
                articles.setdefault(article["url"], article)

        results = list(articles.values())
        return results[:limit] if limit else results

    def __safe_get(self, url: str) -> requests.Response | None:
        """Fetch a URL and return the response, or None on any failure."""
        try:
            response = requests.get(url, timeout=_TIMEOUT)
            response.raise_for_status()
            return response
        except Exception:
            return None

    def __candidate_feed_urls(self) -> list[str]:
        """Collect candidate sitemap/RSS URLs from robots.txt, homepage <link> tags, and common paths."""
        candidates: list[str] = []

        robots = self.__safe_get(f"{self.news_domain}/robots.txt")
        if robots is not None:
            candidates += [
                line.split(":", 1)[1].strip()
                for line in robots.text.splitlines()
                if line.lower().startswith("sitemap:")
            ]

        homepage = self.__safe_get(self.news_domain)
        if homepage is not None:
            soup = BeautifulSoup(homepage.text, "lxml")
            candidates += [
                urljoin(self.news_domain, link.get("href"))
                for link in soup.find_all("link", attrs={"type": re.compile("rss|atom")})
                if link.get("href")
            ]

        if not candidates:
            candidates = [self.news_domain + path for path in _SITEMAP_FALLBACKS]

        # De-duplicate while preserving order, prioritizing anything "news"-related.
        seen = set()
        deduped = []
        for url in candidates:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        deduped.sort(key=lambda url: "news" not in url.lower())

        return deduped[:_MAX_FEEDS]

    def __parse_feed(self, feed_url: str, depth: int) -> list[dict]:
        """Parse a sitemap index, sitemap urlset, or RSS/Atom feed at the given URL."""
        if depth > _MAX_SITEMAP_DEPTH:
            return []

        response = self.__safe_get(feed_url)
        if response is None:
            return []

        soup = self.__safe_parse_xml(response.content)
        if soup is None:
            return []

        if soup.find("sitemapindex") is not None:
            sub_sitemaps = [
                loc.get_text(strip=True)
                for loc in soup.find_all("loc")
                if "news" in loc.get_text(strip=True).lower()
            ]
            articles = []
            for sub_sitemap in sub_sitemaps[:_MAX_FEEDS]:
                articles.extend(self.__parse_feed(sub_sitemap, depth=depth + 1))
            return articles

        if soup.find("urlset") is not None:
            entries = (self.__entry(url_tag, "loc", "title", "publication_date", "lastmod")
                       for url_tag in soup.find_all("url"))
            return [entry for entry in entries if entry is not None]

        if soup.find("rss") is not None or soup.find("feed") is not None:
            entries = (self.__entry(item, "link", "title", "pubdate", "published", "updated")
                       for item in soup.find_all(["item", "entry"]))
            return [entry for entry in entries if entry is not None]

        return []

    @staticmethod
    def __safe_parse_xml(content: bytes) -> BeautifulSoup | None:
        try:
            return BeautifulSoup(content, "xml")
        except Exception:
            return None

    @staticmethod
    def __entry(tag, url_key: str, title_key: str, *date_keys: str) -> dict | None:
        """Build an {url, title, date} dict from a sitemap <url> or feed <item>/<entry> tag."""
        url_tag = tag.find(url_key)
        url = None
        if url_tag is not None:
            url = url_tag.get_text(strip=True) or url_tag.get("href")
        if not url:
            return None

        title_tag = tag.find(title_key)
        date = None
        for date_key in date_keys:
            date_tag = tag.find(date_key)
            if date_tag is not None and date_tag.get_text(strip=True):
                date = date_tag.get_text(strip=True)
                break

        return {
            "url": url,
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "date": date,
        }
