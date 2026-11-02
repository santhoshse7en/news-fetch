"""FetchResult bulk API (1.1)."""

import asyncio
import json
from pathlib import Path

import pytest

from newsfetch import (
    Config,
    FetchError,
    FetchResult,
    NewsFetcher,
    fetch_many,
    fetch_results,
    iter_results,
)
from newsfetch.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "html"
ARTICLE = (FIXTURES / "rich_article.html").read_bytes()


# --- FetchResult ------------------------------------------------------------------------


@pytest.fixture
def mixed(server):
    """One good article, one 404, one unreachable host."""
    server.routes["/good"] = (200, {"Content-Type": "text/html; charset=utf-8"}, ARTICLE)
    return [server.base + "/good", server.base + "/missing", "http://127.0.0.1:9/down"]


def test_fetch_results_keep_order_and_errors(mixed):
    results = fetch_results(mixed, retries=0, timeout=2)
    assert [r.url for r in results] == mixed
    good, missing, down = results
    assert good.ok and good.article.title == "City Council Approves Transit Plan" and good.error is None
    assert not missing.ok and isinstance(missing.error, FetchError) and missing.status == 404
    assert not down.ok and isinstance(down.error, FetchError) and down.status is None
    assert missing.error_dict() == {"type": "FetchError", "message": missing.error.args[0], "status": 404}


def test_fetch_many_unchanged_returns_none_for_failures(mixed):
    articles = fetch_many(mixed, retries=0, timeout=2)
    assert articles[0] is not None and articles[1] is None and articles[2] is None


def test_iter_results_and_progress(mixed):
    with NewsFetcher(Config(retries=0, timeout=2)) as fetcher:
        streamed = {r.url: r.ok for r in fetcher.iter_results(mixed)}
        seen = []
        fetcher.fetch_results(mixed, on_progress=lambda done, total, url, r: seen.append((done, total, r)))
    assert streamed == {mixed[0]: True, mixed[1]: False, mixed[2]: False}
    assert sorted(d for d, _, _ in seen) == [1, 2, 3]
    assert all(total == 3 and isinstance(r, FetchResult) for _, total, r in seen)
    assert list(iter_results([])) == []


def test_fetch_result_unwrap_and_to_dict():
    with NewsFetcher() as fetcher:
        ok = fetcher.fetch_result("https://ex.com/a", html=ARTICLE)
        bad = fetcher.fetch_result("https://ex.com/b", html=b"<html><body></body></html>")
    assert ok.unwrap().title == "City Council Approves Transit Plan"
    assert ok.to_dict()["ok"] is True and ok.to_dict()["error"] is None
    with pytest.raises(Exception, match="Could not extract"):
        bad.unwrap()
    data = bad.to_dict()
    assert data == {"url": "https://ex.com/b", "ok": False, "article": None, "error": bad.error_dict()}
    assert data["error"]["type"] == "ExtractionError"
    json.dumps(ok.to_dict())  # serializable


def test_fetch_results_async(mixed):
    pytest.importorskip("httpx")
    from newsfetch import fetch_many_async, fetch_results_async

    results = asyncio.run(fetch_results_async(mixed, timeout=2))
    assert [r.url for r in results] == mixed
    assert [r.ok for r in results] == [True, False, False]
    assert results[1].status == 404
    assert isinstance(results[2].error, FetchError)
    articles = asyncio.run(fetch_many_async(mixed, timeout=2))
    assert articles[0] is not None and articles[1:] == [None, None]


def test_cli_batch_reports_errors_and_exit_code(server, tmp_path, capsys):
    server.routes["/good"] = (200, {}, ARTICLE)
    urls = tmp_path / "urls.txt"
    urls.write_text(f"{server.base}/good\n{server.base}/missing\n", encoding="utf-8")
    assert main(["batch", str(urls)]) == 0  # partial failure is still success
    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines()]
    errors = [r["error"] for r in rows if "error" in r]
    assert errors == [{"type": "FetchError", "message": f"HTTP 404 for {server.base}/missing", "status": 404}]
    assert "1 ok, 1 failed" in captured.err

    urls.write_text(f"{server.base}/missing\n", encoding="utf-8")
    assert main(["batch", str(urls)]) == 1  # nothing succeeded

