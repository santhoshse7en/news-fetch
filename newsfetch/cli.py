"""Command-line interface for news-fetch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from newsfetch import __version__, discover, extract, fetch
from newsfetch.api import NewsFetcher
from newsfetch.config import Config


def _print_human(article) -> None:
    print(f"Title:       {article.title or ''}")
    print(f"Publisher:   {article.publisher or ''}")
    print(f"Published:   {article.published_at or ''}")
    print(f"Authors:     {', '.join(article.authors) if article.authors else ''}")
    print(f"Confidence:  {article.confidence.overall:.2f}")
    print(f"Page type:   {article.page_type}")
    print(f"URL:         {article.canonical_url or article.url}")
    if article.text:
        preview = article.text.replace("\n", " ")
        print(f"Text:        {preview[:280]}{'…' if len(preview) > 280 else ''}")


def _load_urls(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def _normalize_argv(argv: list[str]) -> list[str]:
    """Allow `news-fetch URL` by mapping to the get subcommand."""
    if not argv:
        return argv
    commands = {"get", "batch", "discover", "-h", "--help", "--version"}
    if argv[0] in commands or argv[0].startswith("-"):
        # Flags-only / known command — if starts with flags and no command, use get
        if argv[0].startswith("-") and argv[0] not in {"-h", "--help", "--version"}:
            return ["get", *argv]
        return argv
    # Bare URL
    return ["get", *argv]


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv = _normalize_argv(raw)

    parser = argparse.ArgumentParser(
        prog="news-fetch",
        description="Python news scraper & article extractor — confidence-aware, no API key.",
    )
    parser.add_argument("--version", action="version", version=f"news-fetch {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    get_p = sub.add_parser("get", help="Fetch a single article URL")
    get_p.add_argument("url", nargs="?", help="Article URL")
    get_p.add_argument("--json", action="store_true", help="Print JSON")
    get_p.add_argument("--html", type=Path, help="Extract from a local HTML file (no network)")
    get_p.add_argument("--proxy", help="HTTP(S) proxy URL")
    get_p.add_argument("--strict", action="store_true")
    get_p.add_argument("--debug", action="store_true")

    batch = sub.add_parser("batch", help="Fetch many URLs from a file; stream JSONL")
    batch.add_argument("urls_file", type=Path, help="Text file with one URL per line")
    batch.add_argument("-o", "--output", type=Path, help="Write JSONL to this file")
    batch.add_argument("--jsonl", action="store_true", help="Also write JSONL to stdout")
    batch.add_argument("--workers", type=int, default=8)
    batch.add_argument("--proxy", action="append", default=[], help="Proxy URL (repeatable)")
    batch.add_argument("--delay", type=float, default=0.0)

    disc = sub.add_parser("discover", help="Discover article URLs from a news site")
    disc.add_argument("site", help="Homepage URL")
    disc.add_argument("--limit", type=int, default=20)
    disc.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "batch":
        urls = _load_urls(args.urls_file)
        cfg = Config(
            max_workers=args.workers,
            request_delay=args.delay,
            proxies=args.proxy or None,
        )
        out_fp = None
        if args.output:
            out_fp = args.output.open("w", encoding="utf-8")
        try:
            with NewsFetcher(cfg) as fetcher:
                for url, article in fetcher.iter_fetch(urls):
                    row = article.to_dict() if article is not None else {"url": url, "error": True}
                    line = json.dumps(row, ensure_ascii=False)
                    if out_fp is not None:
                        out_fp.write(line + "\n")
                        out_fp.flush()
                    if args.jsonl or out_fp is None:
                        print(line)
        finally:
            if out_fp is not None:
                out_fp.close()
        return 0

    if args.command == "discover":
        for item in discover(args.site, limit=args.limit):
            if args.json:
                print(json.dumps(item, ensure_ascii=False))
            else:
                print(item.get("url"))
        return 0

    # get
    if not args.url and not args.html:
        get_p.print_help()
        return 2

    try:
        if args.html:
            html = args.html.read_bytes()
            article = extract(
                html,
                url=args.url or f"file://{args.html}",
                debug=args.debug,
                strict=args.strict,
            )
        else:
            article = fetch(
                args.url,
                debug=args.debug,
                strict=args.strict,
                proxy=args.proxy,
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(article.to_json(indent=2))
    else:
        _print_human(article)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
