[![PyPI version](https://img.shields.io/pypi/v/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![Downloads](https://pepy.tech/badge/news-fetch/month)](https://pepy.tech/project/news-fetch)
[![Python versions](https://img.shields.io/pypi/pyversions/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![License](https://img.shields.io/pypi/l/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch/)
[![Tests](https://img.shields.io/github/actions/workflow/status/santhoshse7en/news-fetch/tests.yml?branch=master&style=flat-square&label=tests)](https://github.com/santhoshse7en/news-fetch/actions/workflows/tests.yml)

# news-fetch

**Python news scraper & article extractor** — extract title, text, Markdown, authors, date, image, and publisher from any news URL. No API key. Confidence scores included.

> **Fetch news. Know why it worked.**

```bash
pip install news-fetch
```

```python
from newsfetch import fetch

article = fetch("https://www.thehindu.com/...")
print(article.title)
print(article.text)
print(article.markdown)             # body with headings, lists, links, images
print(article.authors)
print(article.published_at)
print(article.image)
print(article.confidence.overall)   # 0.0–1.0
print(article.content_source)       # e.g. json-ld.articleBody
```

```bash
news-fetch https://example.com/article
news-fetch https://example.com/article --json
news-fetch https://example.com/article --markdown
news-fetch batch urls.txt -o articles.jsonl
```

---

## Why news-fetch?

A **lightweight alternative** to newspaper3k / newspaper4k / trafilatura wrappers — with its **own extraction engine**, **confidence scores**, and **bulk + proxy** support.

| Feature | news-fetch |
| --- | :---: |
| News article extraction (title, body, authors, date, image) | ✅ |
| Markdown body output for RAG / LLM pipelines (+ optional cleaned HTML) | ✅ |
| Confidence scores + extraction provenance | ✅ |
| Bulk scraping (`fetch_many` / `fetch_results` / CLI JSONL) with per-URL errors | ✅ |
| Proxy + proxy rotation for thousands of URLs | ✅ |
| RSS / sitemap article discovery | ✅ |
| Async (`pip install news-fetch[async]`) | ✅ |
| Optional browser render (`pip install news-fetch[browser]`) | ✅ |
| Disk cache + RFC 9309 robots.txt | ✅ |
| Response size limits, hardened XML parsing | ✅ |
| No API key / no account | ✅ |
| Small deps (`lxml`, `requests`, `python-dateutil`, `cssselect`) | ✅ |

---

## Install

```bash
pip install news-fetch
pip install news-fetch[async]     # httpx async fetch
pip install news-fetch[browser]   # Playwright fallback (then: playwright install chromium)
```

**Requirements:** Python 3.11+

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

### Markdown and HTML output

`article.markdown` is always filled. It is rendered from the article body's DOM node, so it keeps
headings, nested lists, links, images with captions, blockquotes, fenced code and tables; when the
body only exists as text (for example JSON-LD `articleBody` with no matching node) it falls back to
plain paragraphs. `article.sources["markdown"]` tells you which path was used.

```python
article = fetch(url)
print(article.markdown)
# ## Key points
#
# Read the [full **report**](https://example.com/report.pdf) …
#
# - First point
# - Second point

article = fetch(url, include_html=True)
print(article.html)   # cleaned body HTML: no scripts, nav, share widgets or tracking attributes
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

`fetch_many` / `fetch_iter` return `None` for failed URLs. To know *why* a URL failed, use
`fetch_results` / `iter_results`, which return a `FetchResult` per URL:

```python
from newsfetch import fetch_results

for result in fetch_results(urls, max_workers=20):
    if result.ok:
        print(result.article.title)
    else:
        print(result.url, type(result.error).__name__, result.status, result.error)
# result.unwrap() returns the article or raises the captured error; result.to_dict() is JSON-ready
```

`NewsFetcher` has the same methods (`fetch_result`, `fetch_results`, `iter_results`) when you want to
reuse one configured client.

### Proxies

Any HTTP(S) proxy works, and SOCKS (`socks5://`) works with `pip install "requests[socks]"` (sync) or
`"httpx[socks]"` (async). Pass one proxy, or a pool that is rotated round-robin:

```python
from newsfetch import fetch, fetch_results, Config, NewsFetcher

article = fetch(url, proxy="http://user:pass@host:port")

results = fetch_results(urls, proxies=[
    "http://user:pass@p1:8080",
    "http://user:pass@p2:8080",
])

# Separate proxies per scheme
fetcher = NewsFetcher(Config(proxies={"http": "http://host:8080", "https": "http://host:8443"}))
```

```bash
news-fetch get URL --proxy http://user:pass@host:port
news-fetch batch urls.txt --proxy http://p1:8080 --proxy http://p2:8080 --delay 0.2
```

Proxies are useful for large crawls, region-specific editions, or keeping scraping traffic off your
own IP. Keep `request_delay` and `respect_robots=True` on, and follow each site's terms.

Need a proxy provider? [Proxy-Seller](REFERRAL_LINK) (*affiliate*) is one option; its proxy URLs plug
straight into the settings above. Use code `COUPON_CODE` for a discount.
*Disclosure: affiliate link. If you buy through it, the project receives a commission at no extra cost
to you. See [Sponsors & partnerships](#sponsors--partnerships).*

### Strict mode (production pipelines)

```python
from newsfetch import fetch, LowConfidenceExtractionError

try:
    article = fetch(url, strict=True)
except LowConfidenceExtractionError as e:
    print(e.failed_fields, e.confidence.overall)
```

`strict=True` requires title and content confidence ≥ 0.6. Tune it with `min_confidence`,
`min_content_confidence`, `min_title_confidence`, or `require_article_page=True`.

### Discovery (RSS / sitemaps)

```python
from newsfetch import discover

for item in discover("https://www.bbc.com", limit=10):
    print(item["url"], item.get("title"))
```

Discovery reads `Sitemap:` lines in robots.txt, feeds linked from the homepage, and common sitemap
paths. `NewsFetcher(config).discover(site)` reuses the fetcher's user agent, proxies and limits.

### Async

```python
from newsfetch import fetch_async, fetch_many_async, fetch_results_async

article = await fetch_async(url)
articles = await fetch_many_async(urls, max_concurrency=50, proxies=PROXIES)
results = await fetch_results_async(urls, max_concurrency=50)   # list[FetchResult]
```

Requires `pip install news-fetch[async]`.

### CLI

```bash
news-fetch https://example.com/article              # same as: news-fetch get URL
news-fetch get URL --json
news-fetch get URL --markdown                       # article body as Markdown
news-fetch get --html page.html https://example.com/a   # extract a saved page, no network
news-fetch batch urls.txt -o out.jsonl --workers 20 --proxy http://p1:8080 --delay 0.1
news-fetch discover https://www.theguardian.com --limit 10 --json
```

`batch` streams one JSON object per URL. Failed URLs are written as
`{"url": ..., "error": {"type", "message", "status"}}`, a `N ok, M failed` summary goes to stderr,
and the exit code is 1 only when no URL succeeded.

### Cache / robots / browser / size limits

```python
from newsfetch import fetch

fetch(url, cache=True, respect_robots=True)
fetch(url, render=True)                      # needs news-fetch[browser]
fetch(url, browser_fallback=True)            # retry with Playwright if confidence is low
fetch(url, max_bytes=2 * 1024 * 1024)        # cap response size (default 10 MiB, None = no limit)
```

`respect_robots=True` follows [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309): wildcard rules,
longest match wins, and if robots.txt is unreachable (5xx / network error) the fetch is refused.
Response bodies are capped *after* decompression, so compressed "bombs" are rejected too.

### Custom strategy plugin

```python
from newsfetch import NewsFetcher, CallableStrategy
from newsfetch.strategies.base import Candidate

def my_strategy(doc):
    return {"title": [Candidate("Custom", "plugin.custom", 0.99)]}

fetcher = NewsFetcher()
fetcher.register_strategy(CallableStrategy("custom", my_strategy))
```

### Debugging an extraction

```python
article = fetch(url, debug=True)
article.sources                     # {"title": "og:title", "text": "json-ld.articleBody", ...}
article.extraction.content          # winning strategy, score, confidence, candidate count, agreements
article.trace.strategies_tried      # ["json-ld", "opengraph", "meta", "semantic", "dom", ...]
article.trace.candidates            # every candidate considered, with the selected ones marked
```

---

## Configuration

Every option can be passed as a keyword to `fetch`, `extract`, `fetch_many`, `fetch_results`, … or
set on a `Config` for `NewsFetcher(Config(...))`.

| Option | Default | Purpose |
| --- | --- | --- |
| `timeout` | `15.0` | Request timeout (seconds) |
| `retries` | `2` | Retries for connection errors, 429 and 5xx |
| `max_bytes` | `10 MiB` | Max decompressed response size; `None` / `0` = unlimited |
| `user_agent` / `headers` | `news-fetch/1.1 (+…)` / `{}` | Request identity and extra headers |
| `proxy` / `proxies` / `rotate_proxies` | `None` / `None` / `True` | One proxy, or a pool rotated round-robin |
| `max_workers` / `request_delay` | `8` / `0.0` | Bulk concurrency and per-request delay |
| `include_html` | `False` | Fill `article.html` with cleaned body HTML |
| `strict` / `min_confidence` | `False` / `0.0` | Raise `LowConfidenceExtractionError` below thresholds |
| `respect_robots` | `False` | Check robots.txt (RFC 9309) before fetching |
| `cache` / `cache_path` / `cache_ttl` | `False` / `.news-fetch-cache.sqlite` / `86400` | SQLite page cache |
| `render` / `browser_fallback` | `False` / `False` | Playwright rendering (always / only on low confidence) |
| `language` | `None` | Fallback language when the page declares none |
| `debug` | `False` | Attach `article.trace` |

## Errors

All exceptions derive from `NewsFetchError`:

- `FetchError` — HTTP or transport failure (`.url`, `.status`), robots.txt refusal, oversized response
- `ParseError` — the document could not be parsed
- `ExtractionError` — no title or text could be extracted
  - `LowConfidenceExtractionError` — strict-mode gate failed (`.confidence`, `.failed_fields`, `.article`)

## Article fields

| Field | Description |
| --- | --- |
| `url`, `canonical_url` | Requested / final URL and canonical URL (tracking params stripped) |
| `title`, `description` | Headline and summary/standfirst |
| `text` | Body as plain paragraphs |
| `markdown` | Body as Markdown (always filled when there is body text) |
| `html` | Cleaned body HTML (only with `include_html=True`) |
| `authors`, `publisher`, `section` | Bylines, publication, section/category |
| `published_at`, `modified_at` | Timezone-aware `datetime`s |
| `language` | Primary language subtag (`en`, `de`, `fil`, …) |
| `image`, `images` | Lead image URL |
| `keywords`, `summary` | Page keywords (or frequency-based), lead-sentence summary |
| `word_count`, `reading_time_minutes` | Body length |
| `page_type`, `is_article` | `article`, `homepage`, `category`, `live_blog`, `video`, `opinion`, … |
| `confidence` | Per-field and `overall` scores (0.0–1.0) |
| `sources`, `extraction` | Which strategy produced each field, and per-field evidence |
| `trace` | Full candidate trace (only with `debug=True`) |

```python
article.to_dict()
article.to_json(indent=2)
```

## Migrating from news-fetch ≤ 0.4

The old `newsfetch.news.Newspaper` class still works but is deprecated:

```python
# before
from newsfetch.news import Newspaper
news = Newspaper(url=url)
news.headline, news.article, news.date_publish

# now
from newsfetch import fetch
article = fetch(url)
article.title, article.text, article.published_at
```

---

## Contributing

Development uses [uv](https://docs.astral.sh/uv/) (Python 3.11+):

```bash
uv sync                 # .venv with the package + dev dependency group, pinned by uv.lock
uv run pytest
uv run ruff check .
uv run python benchmarks/run_benchmark.py
uv build                # sdist + wheel into dist/
```

CI runs ruff, tests on Python 3.11–3.14 (Linux, plus macOS), the lowest supported dependency
versions, and a smoke test of the built wheel. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
workflow, test conventions and release steps, and the [Code of Conduct](CODE_OF_CONDUCT.md).

**Security issues:** please report them privately as described in [SECURITY.md](SECURITY.md), not in
public issues.

---

## Sponsors & partnerships

news-fetch is free, MIT-licensed and maintained in spare time. Partnerships fund maintenance, new
extractors and faster fixes — and they never change what the library does by default.

### Ways to work together

| Partnership | What it looks like | Good fit for |
| --- | --- | --- |
| **Sponsorship** | Your logo/name in this README and thanks in release notes | Companies and teams running news-fetch in production |
| **Integration partner** | A documented guide or example showing news-fetch with your product | Proxy networks, rendering/browser APIs, vector databases and RAG platforms, news-data and media-monitoring tools |
| **Affiliate program** | A clearly labelled referral link in the matching docs section (e.g. proxies next to proxy rotation) | Proxy and hosting providers relevant to scraping workloads |
| **Commercial support** | Custom site extractors, priority fixes, integration help, private consulting | Teams with specific sources or SLAs |
| **Research & education** | Collaboration, datasets and benchmarks, a listing of your paper or course | Universities, journalism and NLP research groups |

### Current sponsors & partners

| Partner | Type | Where it appears |
| --- | --- | --- |
| [Proxy-Seller](REFERRAL_LINK) | Affiliate (proxy provider) | [Proxies](#proxies) |

Want to sponsor or partner? [Get in touch](#get-in-touch). Using news-fetch in a product or a paper?
Open a pull request adding it to a "Used by" list here.

### Principles

These hold for every sponsorship, integration and affiliate deal:

- **Open source stays open.** The library stays MIT-licensed; no feature is paywalled or sponsor-only.
- **Neutral defaults.** No partner service is a required dependency, a default proxy, or a default endpoint.
  Traffic only goes where *you* point it.
- **No tracking.** No telemetry, ads, referral parameters or sponsored content are added to the code,
  to requests, or to extracted articles.
- **Labelled links.** Affiliate and sponsored links are always marked as such (*affiliate* / *sponsored*)
  and listed in this section.
- **Independent results.** Benchmarks, comparisons and recommendations are not for sale.
- **Responsible scraping only.** We don't partner with services whose purpose is bypassing paywalls,
  logins, CAPTCHAs or other access controls. Integrations must respect site terms, robots.txt and the law.

### Affiliate disclosure

Some links in this project's documentation may be affiliate links, marked *affiliate*. If you buy
through one, the maintainer may earn a commission at no extra cost to you. Affiliate relationships
never affect the code, the defaults, or which tools are recommended.

### Get in touch

Email **santhoshse7en@gmail.com** with the subject `news-fetch partnership` and include:

- who you are (company/organisation and a link),
- the kind of partnership from the table above,
- how you use or plan to use news-fetch.

For bugs and feature requests, please use [GitHub Issues](https://github.com/santhoshse7en/news-fetch/issues) instead.

---

## Links

- **PyPI:** https://pypi.org/project/news-fetch/
- **Docs:** https://santhoshse7en.github.io/newsfetch_doc/
- **GitHub:** https://github.com/santhoshse7en/news-fetch
- **Issues:** https://github.com/santhoshse7en/news-fetch/issues
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Partnerships:** [Sponsors & partnerships](#sponsors--partnerships)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) · **Security:** [SECURITY.md](SECURITY.md)

MIT License · Built for developers who need reliable Python news scraping without an API.
