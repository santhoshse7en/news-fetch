# Contributing to news-fetch

Thanks for helping! Bug reports, failing pages, fixes, new extraction strategies and docs
improvements are all welcome. By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

> Found a security issue? Please **don't** open an issue. Follow [SECURITY.md](SECURITY.md) instead.

## Reporting bugs and extraction problems

Open a [GitHub issue](https://github.com/santhoshse7en/news-fetch/issues) with:

- `news-fetch --version`, your Python version and OS,
- a minimal snippet, the full traceback (if any), and what you expected,
- for **wrong or missing fields**: the URL **and** the page HTML saved to a file (sites change, and a
  saved page lets us reproduce the problem), plus the output of `fetch(url, debug=True).sources`.

## Development setup

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/santhoshse7en/news-fetch.git
cd news-fetch
uv sync                                  # .venv with the package (editable) + dev group, pinned by uv.lock
uv run pytest                            # test suite
uv run ruff check .                      # lint
uv run python benchmarks/run_benchmark.py
```

To change dependencies, edit `pyproject.toml` and run `uv lock`. Commit the updated `uv.lock`, because
CI uses `uv sync --locked` and fails if the lockfile is stale.

## Project layout

| Path | What lives there |
| --- | --- |
| `newsfetch/api.py`, `async_api.py` | Public entry points: `fetch`, `extract`, `fetch_results`, `NewsFetcher`, async variants |
| `newsfetch/config.py` | `Config`, the one place every option is defined |
| `newsfetch/client/` | HTTP client (retries, size limit), proxies, robots.txt (RFC 9309), disk cache, browser rendering |
| `newsfetch/strategies/` | Extraction strategies: JSON-LD, OpenGraph, meta, semantic HTML, DOM heuristic, plugins |
| `newsfetch/extract/` | Pipeline that collects candidates, ranks them, and computes confidence |
| `newsfetch/output/` | Body cleaning, `article.html` and `article.markdown` rendering |
| `newsfetch/discover/` | RSS / Atom / sitemap discovery |
| `newsfetch/models/` | `Article`, `FetchResult`, evidence and confidence types |
| `tests/` | pytest suite; `tests/fixtures/html/` holds saved pages |
| `benchmarks/` | Fixture benchmark (`expectations.json`) |

## Making a change

1. **Open an issue first** for anything bigger than a small fix (new features, new public API, behaviour
   changes) so we can agree on the approach.
2. Branch from `master`.
3. **Add tests.**
   - Every bug fix needs a regression test that fails without the fix.
   - **Tests never touch the internet.** Use `extract(html, url=...)` with an HTML string or a fixture,
     or the `server` fixture in `tests/conftest.py`, a local HTTP server where you set
     `server.routes["/path"] = (status, headers, body)` and inspect `server.seen`.
   - For extraction fixes, save a **trimmed, anonymised** page under `tests/fixtures/html/`. Keep only the
     markup needed to reproduce the problem, and replace real names and domains with example ones
     (`example.com`, `.test`). If it is a general case, add it to `benchmarks/expectations.json`
     (`url`, `title_contains`, `text_contains`) too.
4. **Keep the style.** Ruff enforces the rules (line length 120, Python 3.11 syntax). Add type hints on
   public functions, and keep comments short and only where the code isn't obvious.
5. **Update the docs.** Add an entry under the unreleased version in [CHANGELOG.md](CHANGELOG.md)
   (Added / Changed / Fixed / Removed). For user-visible behaviour, update the README too. New `Config`
   options also go in the README's Configuration table.
6. Run `uv run pytest` and `uv run ruff check .` before pushing.

### Design guidelines

- **No new runtime dependencies** without discussion. The core is intentionally small (`lxml`,
  `cssselect`, `requests`, `python-dateutil`); optional features go behind an extra like `[async]` or
  `[browser]`.
- **Keep the public API stable.** Add new functions or options instead of changing existing return
  types. Breaking changes need a major version.
- **Everything is configurable through `Config`.** A new option is a dataclass field with a safe
  default, and nothing should require a third-party service.
- **New extraction strategies** return `{field: [Candidate(value, source, score)]}`. Use a descriptive
  `source` (it appears in `article.sources`), and pick scores relative to the existing strategies.
  For one-off site rules, prefer a plugin (`register_strategy`) over changing the core.
- **Treat fetched content as untrusted.** Keep the size limits and hardened parsers in place (see
  [SECURITY.md](SECURITY.md)).

## Commits and pull requests

- Write commit subjects in the imperative mood, under ~72 characters ("Fix date parsing for RFC 822
  feeds"), with a body explaining *why* when it isn't obvious. Keep unrelated changes in separate commits.
- In the pull request, describe the problem, the fix, and how you tested it, and link the issue.
- CI must pass: ruff, tests on Python 3.11–3.14 (Linux, plus macOS), the lowest supported dependency
  versions, and a smoke test of the built wheel.
- A maintainer will review. Small, focused PRs get merged fastest.

## Releasing (maintainers)

1. Bump the version in `pyproject.toml`, `newsfetch/__init__.py` (`__version__`), the user agent in
   `newsfetch/config.py`, and `tests/test_api.py`, then run `uv lock`.
2. In `CHANGELOG.md`, replace "Unreleased" with the release date.
3. Merge to `master`, tag `vX.Y.Z`, and publish a GitHub release. The **Publish to PyPI** workflow
   builds with `uv build` and uploads via PyPI Trusted Publishing.

## License

By contributing, you agree that your contributions are licensed under the project's
[MIT License](LICENSE).
