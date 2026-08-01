# Changelog

All notable changes to this project are documented in this file.

## [0.4.1]

### Fixed
- `SoupHandler` now unwraps the `{"@context": ..., "@graph": [...]}` JSON-LD shape used by sites like BBC. Previously the JSON-LD fallback for `publication`, `category`, `date_publish`, and `date_modify` silently returned nothing on any site using this (common) shape.
- `ArticleHandler.date_publish` now also checks the nested `article.published_time` key that Open Graph article tags actually populate, matching how `category` already looked up `article.section`.
- `Newspaper.authors` no longer returns `None` when neither the article engine nor the JSON-LD fallback has authors; it now consistently returns `[]`, matching its declared type.
- Removed dead `max_keywords` parameter from `ArticleHandler.__process_keywords` (never called with a value).
- Deduplicated the identical `__safe_execute` helper that was copy-pasted across `ArticleHandler` and `SoupHandler` into a shared `newsfetch.helpers.safe_execute`.

### Changed
- `pyproject.toml`'s `Homepage` and `Documentation` project URLs pointed at a GitHub Pages site that returns 404; `Homepage` now points at the GitHub repository and the dead `Documentation` entry was removed.
- Bumped `newspaper4k` to `0.9.6` and `twine` (dev) to `7.0.0` in the pinned requirements files.
- Added `Typing :: Typed` classifier (the package ships `py.typed`).
- README: fixed a dependency-list omission (`lxml-html-clean`), a mislabeled "Repository" link, and stale sample output; added GitHub stats badges, a table of contents, and a feature comparison table.

## [0.4.0] and earlier

See the [GitHub release history](https://github.com/santhoshse7en/news-fetch/commits/master) — changelog tracking starts at 0.4.1.
