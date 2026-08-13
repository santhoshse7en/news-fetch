"""CLI and streaming API tests."""

from pathlib import Path

from newsfetch import extract, fetch_iter
from newsfetch.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "html"


def test_cli_html_json(tmp_path, capsys):
    html = FIXTURES / "rich_article.html"
    code = main(["get", "--html", str(html), "--json", "https://www.example.com/news/x"])
    assert code == 0
    out = capsys.readouterr().out
    assert "City Council" in out
    assert "confidence" in out


def test_cli_batch_jsonl(tmp_path, capsys):
    # batch needs network for URLs; instead verify help/empty handling via urls of file:// style
    # Use extract path indirectly: batch always fetches; create empty urls file
    urls = tmp_path / "urls.txt"
    urls.write_text("# no urls\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    code = main(["batch", str(urls), "-o", str(out)])
    assert code == 0
    assert out.exists()


def test_fetch_iter_offline_via_extract_pattern():
    # fetch_iter is network-bound; smoke-test import + generator protocol with empty list
    assert list(fetch_iter([])) == []


def test_og_semantic_fixture():
    html = (FIXTURES / "og_semantic.html").read_text(encoding="utf-8")
    article = extract(html, url="https://wire.example/2025/11/02/markets-rally")
    assert "Markets Rally" in (article.title or "")
    assert article.published_at is not None
    assert "inflation" in (article.text or "").lower()


def test_homepage_not_article():
    html = (FIXTURES / "homepage_like.html").read_text(encoding="utf-8")
    article = extract(html, url="https://news.example.com/")
    assert article.is_article is False or article.page_type == "homepage"
