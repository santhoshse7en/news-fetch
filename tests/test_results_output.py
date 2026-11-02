"""FetchResult bulk API and Markdown / HTML body output (1.1)."""

import asyncio
import json
from pathlib import Path

import pytest

from newsfetch import (
    Config,
    FetchError,
    FetchResult,
    NewsFetcher,
    extract,
    fetch_many,
    fetch_results,
    iter_results,
)
from newsfetch.cli import main
from newsfetch.output import clean_body, to_markdown
from newsfetch.parser.html import Document

FIXTURES = Path(__file__).parent / "fixtures" / "html"
ARTICLE = (FIXTURES / "rich_article.html").read_bytes()


def _md(html: str, selector: str = "article", base_url: str = "https://ex.com/news/a") -> str:
    doc = Document.from_html(html, base_url=base_url)
    return to_markdown(clean_body(doc.css(selector)[0], base_url=base_url))


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


# --- Markdown / HTML output -------------------------------------------------------------


def test_markdown_always_html_opt_in():
    article = extract(ARTICLE, url="https://www.example.com/news/x")
    assert article.markdown.startswith("# City Council Approves Transit Plan")
    assert "transit expansion" in article.markdown
    assert article.html is None
    assert article.to_dict()["markdown"] == article.markdown

    with_html = extract(ARTICLE, url="https://www.example.com/news/x", include_html=True)
    assert with_html.html.startswith("<article>")
    assert "<script" not in with_html.html and "class=" not in with_html.html


def test_markdown_for_each_content_source():
    for name, source in [
        ("rich_article", "dom:json-ld.articleBody"),  # JSON-LD text mapped back to its DOM node
        ("og_semantic", "dom:semantic.itemprop.articleBody"),
        ("heuristic_only", "dom:heuristic.dom-score"),
    ]:
        article = extract((FIXTURES / f"{name}.html").read_bytes(), url="https://www.example.com/news/x")
        assert article.sources["markdown"] == source, name
        assert article.markdown and len(article.markdown) >= len(article.text) * 0.8, name


def test_markdown_falls_back_to_text_without_dom_node():
    body = "First paragraph of the story with enough words to count here. " * 3
    html = (
        '<html><head><script type="application/ld+json">'
        + json.dumps({"@type": "NewsArticle", "headline": "Only JSON", "articleBody": f"{body}\n\nSecond *para*."})
        + "</script></head><body><p>Unrelated page chrome.</p></body></html>"
    )
    article = extract(html, url="https://ex.com/a", include_html=True)
    assert article.sources["markdown"] == "text"
    assert article.markdown.endswith("Second \\*para\\*.")
    assert article.html.startswith("<p>First paragraph") and "<p>Second *para*.</p>" in article.html


def test_markdown_structure():
    md = _md(
        """<article>
        <h2>Key points</h2>
        <p>Read the <a href="/report.pdf">full <b>report</b></a> or <em>skim</em>.<br>Next line.</p>
        <ul><li>One</li><li>Two<ul><li>Nested</li></ul></li></ul>
        <ol start="3"><li>Three</li><li>Four</li></ol>
        <blockquote><p>Quoted.</p><p>Again.</p></blockquote>
        <figure><img data-src="/a.jpg" alt="Photo"><figcaption>Caption</figcaption></figure>
        <pre><code class="language-python">x = 1</code></pre>
        <table><tr><th>Team</th><th>Score</th></tr><tr><td>A|B</td><td>3</td></tr></table>
        </article>"""
    )
    assert md == "\n\n".join(
        [
            "## Key points",
            "Read the [full **report**](https://ex.com/report.pdf) or *skim*.  \nNext line.",
            "- One\n- Two\n  - Nested",
            "3. Three\n4. Four",
            "> Quoted.\n>\n> Again.",
            "![Photo](https://ex.com/a.jpg)",
            "*Caption*",
            "```python\nx = 1\n```",
            "| Team | Score |\n|---|---|\n| A\\|B | 3 |",
        ]
    )


def test_markdown_escaping():
    md = _md("<article><p>5 * 3 = 15_000 [sic]</p><p>1. not a list</p><p># not a heading</p></article>")
    assert md == "5 \\* 3 = 15\\_000 \\[sic\\]\n\n1\\. not a list\n\n\\# not a heading"


def test_clean_body_removes_boilerplate_keeps_text():
    html = """<article>
      <script>alert(1)</script><p hidden>secret</p><p style="display: none">hidden too</p>
      <div class="share-buttons"><a href="https://fb.com/x">Share</a></div>
      <p>Before <span>span</span> after<!-- c --> <a href="javascript:void(0)">click</a> end.</p>
      <aside>Related</aside><img src="data:image/png;base64,xx">
    </article>"""
    assert _md(html) == "Before span after click end."
    doc = Document.from_html(html)
    node = doc.css("article")[0]
    clean_body(node)
    assert node.cssselect("script")  # the source document is not modified
