# Security Policy

news-fetch downloads and parses content from websites you don't control, so it treats every
response as untrusted input. This document explains how to report a vulnerability and what
protections the library provides.

## Supported versions

Security fixes are released for the latest minor version. Please upgrade before reporting.

| Version | Supported |
| --- | :---: |
| 1.1.x (latest) | ✅ |
| 1.0.x and older | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Email **santhoshse7en@gmail.com** with the subject `news-fetch security` and include:

- the affected version (`news-fetch --version`) and Python version,
- a description of the issue and its impact,
- steps to reproduce: ideally a minimal script plus the HTML / XML / HTTP response that triggers it
  (attach files rather than linking to a live site),
- any suggested fix, if you have one.

### What to expect

news-fetch is maintained by volunteers, so these are targets rather than guarantees:

| Step | Target |
| --- | --- |
| Acknowledgement of your report | within 7 days |
| Initial assessment (confirmed / not a vulnerability / need more info) | within 14 days |
| Fix released for confirmed issues | within 90 days, sooner for severe issues |

We'll keep you updated, agree on a disclosure date with you, and credit you in the release notes and
[CHANGELOG](CHANGELOG.md) unless you prefer to stay anonymous. Please give us a reasonable chance to
release a fix before disclosing publicly.

## Scope

**In scope**, vulnerabilities in news-fetch's own code, for example:

- XML or HTML parsing issues: entity expansion, external entity (XXE) loading, parser-triggered
  network or file access, in sitemaps, feeds or pages,
- bypassing `max_bytes`, including decompression bombs,
- denial of service from crafted input: catastrophic regex backtracking, unbounded recursion or
  memory use while extracting,
- robots.txt handling that lets `respect_robots=True` fetch disallowed URLs,
- unsafe handling of local files (`--html`), the disk cache, or CLI output,
- injection into `article.html` / `article.markdown` beyond what the cleaning step documents, such as
  surviving `<script>` elements, event-handler attributes or `javascript:` links.

**Out of scope:**

- sites blocking, rate-limiting or serving different content to news-fetch, and extraction quality
  in general (please open a normal issue),
- vulnerabilities in dependencies (lxml, requests, urllib3, httpx, Playwright…) that news-fetch
  doesn't make worse. Report those upstream, though we welcome a heads-up if news-fetch needs a
  minimum-version bump,
- fetching a URL the caller passed in, including internal addresses. news-fetch fetches what you ask
  it to (see "Running on untrusted URLs" below),
- legal questions about scraping a particular site.

## Built-in protections

| Risk | Protection |
| --- | --- |
| Huge or compressed "bomb" responses | Bodies are streamed and capped after decompression (`max_bytes`, default 10 MiB); robots.txt is capped at 500 KiB |
| XML entity expansion / XXE | Sitemaps and feeds are parsed with entity resolution, DTD loading and network access disabled |
| Scripts and tracking in output | `article.html` drops scripts, iframes, forms, hidden elements and all non-allow-listed attributes; `javascript:` / `data:` links are removed |
| Unbounded retries | Retries are capped (`retries`, default 2), and `Retry-After` waits are clamped to 60 s |
| Telemetry | None. news-fetch only contacts the URLs you give it (plus robots.txt and feeds when you enable those features) |

## Running on untrusted URLs

If your application fetches URLs supplied by users or by third-party feeds:

- **Restrict network egress.** news-fetch does not block private, loopback or cloud-metadata
  addresses, and it follows redirects. To prevent server-side request forgery (SSRF), validate URLs
  and resolved IPs before calling `fetch`, or run the fetcher where it can't reach internal services.
- **Keep the limits on.** Leave `max_bytes` enabled and set a `timeout` suited to your workload.
- **Be careful with `render=True` / `browser_fallback=True`.** These load the page in headless Chromium
  and run its JavaScript. Keep Playwright up to date and isolate the browser process (container,
  sandbox, no credentials).
- **Treat output as untrusted.** `article.html` is cleaned, not sanitized for every context. Run it
  through your own HTML sanitizer before showing it in a browser, and escape `article.text` /
  `article.markdown` like any user content.
- **Keep the cache private.** `cache=True` stores raw page bodies in a local SQLite file
  (`.news-fetch-cache.sqlite` by default). Put it somewhere other users can't read or write.
