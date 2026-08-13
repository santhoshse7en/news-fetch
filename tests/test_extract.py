"""Unit tests for offline HTML extraction fixtures."""

from __future__ import annotations

from pathlib import Path

from newsfetch import extract
from newsfetch.config import Config
from newsfetch.extract import Extractor
from newsfetch.normalize.url import canonicalize

FIXTURES = Path(__file__).parent / "fixtures" / "html"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_rich_article_jsonld_and_og():
    article = extract(_html("rich_article.html"), url="https://www.example.com/news/transit-plan?utm_source=x")
    assert article.title == "City Council Approves Transit Plan"
    assert "transit expansion" in (article.text or "").lower()
    assert article.authors == ["Jane Reporter"]
    assert article.published_at is not None
    assert article.published_at.year == 2024
    assert article.image == "https://cdn.example.com/transit.jpg"
    assert article.publisher == "Example News"
    assert article.section == "Local"
    assert article.canonical_url == "https://www.example.com/news/transit-plan"
    assert "utm_source" not in (article.canonical_url or "")
    assert article.title_source
    assert "json-ld" in article.title_source
    assert article.content_source
    assert article.word_count > 40


def test_jsonld_graph_shape():
    article = extract(_html("jsonld_graph.html"), url="https://www.bbc.test/news/climate")
    assert article.title == "Ministers Debate Climate Targets"
    assert article.authors == ["Alex Smith"]
    assert article.publisher == "BBC Test"
    assert article.published_at is not None
    assert "westminster" in (article.text or "").lower()


def test_heuristic_only_page():
    article = extract(_html("heuristic_only.html"), url="https://news.example.org/2024/03/01/harbor-signal")
    assert "Mysterious Signal" in (article.title or "")
    assert "harbor" in (article.text or "").lower()
    assert article.published_at is not None  # from URL
    assert article.date_source == "url.date"
    assert article.content_source and "heuristic" in article.content_source


def test_debug_trace():
    article = extract(_html("rich_article.html"), url="https://www.example.com/a", debug=True)
    assert article.trace is not None
    assert "json-ld" in article.trace.strategies_tried
    assert any(c.field == "title" for c in article.trace.candidates)


def test_canonicalize_strips_tracking():
    url = canonicalize("https://Example.com/path?utm_campaign=x&id=1#frag")
    assert url == "https://example.com/path?id=1"


def test_to_dict_serializable():
    article = extract(_html("rich_article.html"), url="https://www.example.com/a")
    data = article.to_dict()
    assert isinstance(data["published_at"], str)
    assert data["title"]


def test_extractor_config_min_length():
    cfg = Config(min_text_length=10, debug=True)
    article = Extractor(cfg).extract(_html("heuristic_only.html"), "https://example.com/x")
    assert article.text
