# Changelog

All notable changes to this project are documented in this file.

## [1.1.0]

### Added
- `Config.max_bytes` (default 10 MiB): response bodies are streamed and capped after decompression
  (sync and async), protecting against oversized pages and gzip bombs. `None`/`0` disables it.
- RFC 9309 robots.txt support: `*` / `$` wildcards, longest-match precedence (allow wins ties),
  product-token group matching with merged groups, percent-encoding normalization, 500 KiB cap.
  New `RobotsRules` and `RobotsCache.check()` returning a `RobotsDecision(allowed, reason)`.
- `discover(..., client=HttpClient)`; `NewsFetcher.discover` reuses the fetcher's client.
- `FetchResult(url, article, error)` with `.ok`, `.status`, `.unwrap()`, `.to_dict()`, returned by new
  `fetch_results` / `iter_results`, `NewsFetcher.fetch_result` / `fetch_results` / `iter_results` and
  `fetch_results_async`. Existing `fetch_many` / `fetch_iter` / `fetch_many_async` are unchanged.
- `Article.markdown`: article body as Markdown (headings, lists, links, images, blockquotes, code,
  GFM tables), always filled — rendered from the content DOM node, or from plain text when the body
  only exists as text (e.g. JSON-LD `articleBody` with no matching node). `sources["markdown"]` says which.
- `Article.html` is now filled with cleaned body HTML when `Config(include_html=True)`.
- CLI: `news-fetch get --markdown`.
- CI test workflow: Python 3.11–3.14 (+ macOS), lowest-dependency job, wheel smoke test, ruff;
  Dependabot for SHA-pinned actions.

### Changed
- **Python 3.11+ required** (3.10 reached end of life in October 2026).
- Development uses [uv](https://docs.astral.sh/uv/) with a committed `uv.lock`; dev tools moved to a
  PEP 735 `[dependency-groups]` table. The `dev` install extra and `requirements*.txt` are removed.
  Publishing builds with `uv build`.
- CLI `batch`: failed URLs are written as `{"url": ..., "error": {"type", "message", "status"}}`
  (was `"error": true`), a `N ok, M failed` summary goes to stderr, and the exit code is 1 when no URL succeeded.
- `fetch_many_async` now runs on `asyncio.TaskGroup`.
- **robots.txt (`respect_robots=True`)**: 5xx, 429 and network errors now mean "unreachable" →
  fetch disallowed (previously allowed). 4xx still means no restrictions. Error messages state the reason.
- robots.txt and discovery requests go through `HttpClient`: configured user agent (no longer
  `python-requests`), proxies, retries and size limits apply.
- Sitemap/feed XML is parsed with entity expansion, DTD loading and network access disabled.
- User agent bumped to `news-fetch/1.1`.

### Fixed
- `<html lang>` was never detected; language tags are reduced to the BCP 47 primary subtag
  (`fil` no longer becomes `fi`).
- `DiskCache` is now thread-safe (`fetch_many(cache=True)` raised sqlite `InterfaceError`).
- Retries no longer multiply (`retries=2` made 9 connection attempts; now 3).
- Dates missing a year, month or day are rejected instead of being completed from today.
- Keyword extraction works for non-Latin scripts.
- `fetch_iter` / `iter_fetch` stop fetching when the consumer stops early.
- A missing `cssselect` install now raises instead of silently matching nothing.

### Removed
- Unused internals: `heuristic.iter_images_near`, `Extractor.extract_from_nodes`.

## [1.0.0]

### Added
- Production-stable release of the independent extraction engine.
- CLI: `news-fetch`, `news-fetch batch` (JSONL), `news-fetch discover`.
- `fetch_iter` for memory-conscious streaming bulk results.
- Strategy plugin API: `register_strategy` / `ExtractionStrategy` / `CallableStrategy`.
- Optional browser rendering: `pip install news-fetch[browser]` + `render=True` / `browser_fallback=True`.
- Disk cache (`cache=True`) and `respect_robots=True`.
- HTTP 429 `Retry-After` handling in the sync client.
- Extra HTML regression fixtures.

### Changed
- Version / user-agent bumped to 1.0; classifier set to Production/Stable.
- README optimized for PyPI discoverability (news scraper / article extractor queries).
- In-repo `docs/` removed (documentation lives in a separate repository).

## [0.6.0]

### Added
- Evidence → rank → confidence architecture (`article.confidence`, `article.extraction`).
- Page-type detection and strict / threshold gates.
- `LowConfidenceExtractionError`, `article.to_json()`.

## [0.5.1]

### Added
- Proxy / proxy pools, rotation, `request_delay`, progress callbacks, `iter_fetch`.

## [0.5.0]

### Changed
- Independent extraction engine; removed `newspaper4k` as the core scraper.
