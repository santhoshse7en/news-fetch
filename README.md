[![PyPI version](https://img.shields.io/pypi/v/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![Downloads](https://pepy.tech/badge/news-fetch/month)](https://pepy.tech/project/news-fetch)
[![Python versions](https://img.shields.io/pypi/pyversions/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![License](https://img.shields.io/pypi/l/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch/)
[![CI](https://img.shields.io/github/actions/workflow/status/santhoshse7en/news-fetch/ci.yml?style=flat-square)](https://github.com/santhoshse7en/news-fetch/actions)

# news-fetch

**Python news scraper & article extractor** — extract title, text, authors, date, image, and publisher from any news URL. No API key. Confidence scores included.

> **Fetch news. Know why it worked.**

```bash
pip install news-fetch
```

```python
from newsfetch import fetch

article = fetch("https://www.thehindu.com/...")
print(article.title)
print(article.text)
print(article.authors)
print(article.published_at)
print(article.image)
print(article.confidence.overall)   # 0.0–1.0
print(article.content_source)       # e.g. json-ld.articleBody
```

```bash
news-fetch https://example.com/article
news-fetch https://example.com/article --json
news-fetch batch urls.txt -o articles.jsonl
```

---

## Why news-fetch?

A **lightweight alternative** to newspaper3k / newspaper4k / trafilatura wrappers — with its **own extraction engine**, **confidence scores**, and **bulk + proxy** support.

| Feature | news-fetch |
| --- | :---: |
| News article extraction (title, body, authors, date, image) | ✅ |
| Confidence scores + extraction provenance | ✅ |
| Bulk scraping (`fetch_many` / `fetch_iter` / CLI JSONL) | ✅ |
| Proxy + proxy rotation for thousands of URLs | ✅ |
| RSS / sitemap article discovery | ✅ |
| Async (`pip install news-fetch[async]`) | ✅ |
| Optional browser render (`pip install news-fetch[browser]`) | ✅ |
| Disk cache + robots.txt respect | ✅ |
| No API key / no account | ✅ |
| Small deps (`lxml`, `requests`, `python-dateutil`, `cssselect`) | ✅ |

---

## Install

```bash
pip install news-fetch
pip install news-fetch[async]     # httpx async fetch
pip install news-fetch[browser]   # Playwright fallback (then: playwright install chromium)
```

**Requirements:** Python 3.10+

---

## Quick start

### Single URL

```python
from newsfetch import fetch

article = fetch(url)
print(article.title, article.text, article.confidence.overall)
```

### From HTML (no network)

```python
from newsfetch import extract

article = extract(html_bytes, url="https://example.com/story")
```

### Bulk scraping + proxies

```python
from newsfetch import fetch_many, fetch_iter

results = fetch_many(
    urls,
    max_workers=20,
    proxies=["http://user:pass@p1:8080", "http://user:pass@p2:8080"],
    request_delay=0.05,
)

for url, article in fetch_iter(urls, max_workers=16):
    if article:
        print(article.title)
```

### Strict mode (production pipelines)

```python
from newsfetch import fetch, LowConfidenceExtractionError

try:
    article = fetch(url, strict=True)
except LowConfidenceExtractionError as e:
    print(e.failed_fields, e.confidence.overall)
```

### Discovery (RSS / sitemaps)

```python
from newsfetch import discover

for item in discover("https://www.bbc.com", limit=10):
    print(item["url"], item.get("title"))
```

### Async

```python
from newsfetch import fetch_async, fetch_many_async

article = await fetch_async(url)
articles = await fetch_many_async(urls, max_concurrency=50, proxies=PROXIES)
```

### CLI

```bash
news-fetch https://example.com/article
news-fetch get URL --json
news-fetch batch urls.txt -o out.jsonl --workers 20
news-fetch discover https://www.theguardian.com --limit 10
```

### Cache / robots / browser

```python
from newsfetch import fetch, Config, NewsFetcher

fetch(url, cache=True, respect_robots=True)
fetch(url, render=True)                      # needs news-fetch[browser]
fetch(url, browser_fallback=True)            # retry with Playwright if confidence is low
```

### Custom strategy plugin

```python
from newsfetch import NewsFetcher, CallableStrategy
from newsfetch.strategies.base import Candidate

def my_strategy(doc):
    return {"title": [Candidate("Custom", "plugin.custom", 0.99)]}

fetcher = NewsFetcher()
fetcher.register_strategy(CallableStrategy("custom", my_strategy))
```

---

## Article fields

`url` · `canonical_url` · `title` · `description` · `text` · `authors` · `published_at` · `modified_at` · `publisher` · `language` · `image` · `keywords` · `section` · `summary` · `word_count` · `reading_time_minutes` · `page_type` · `is_article` · `confidence` · `extraction` · `sources`

```python
article.to_dict()
article.to_json()
```

---

## Links

- **PyPI:** https://pypi.org/project/news-fetch/
- **Docs:** https://santhoshse7en.github.io/newsfetch_doc/
- **GitHub:** https://github.com/santhoshse7en/news-fetch
- **Issues:** https://github.com/santhoshse7en/news-fetch/issues
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

MIT License · Built for developers who need reliable Python news scraping without an API.
