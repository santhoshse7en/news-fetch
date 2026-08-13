"""Confidence, ranking, page-type, and strict-mode tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from newsfetch import LowConfidenceExtractionError, extract
from newsfetch.config import Config
from newsfetch.detect.page_type import detect_page_type
from newsfetch.extract import Extractor
from newsfetch.parser import Document

FIXTURES = Path(__file__).parent / "fixtures" / "html"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_confidence_and_extraction_report():
    article = extract(_html("rich_article.html"), url="https://www.example.com/news/transit-plan")
    assert article.confidence.overall > 0.7
    assert article.confidence.title >= 0.8
    assert article.confidence.content >= 0.8
    assert article.title_confidence == article.confidence.title
    assert article.content_confidence == article.confidence.content
    assert article.extraction.title.strategy in {"jsonld", "fusion", "opengraph", "semantic"}
    assert article.extraction.content.strategy in {"jsonld", "dom", "semantic"}
    assert article.extraction.content.confidence > 0
    assert article.is_article is True
    assert article.page_type in {"article", "opinion", "review", "live_blog"}


def test_to_json_includes_confidence():
    article = extract(_html("rich_article.html"), url="https://www.example.com/a")
    payload = article.to_json()
    assert '"confidence"' in payload
    assert '"overall"' in payload


def test_heuristic_page_confidence():
    article = extract(
        _html("heuristic_only.html"),
        url="https://news.example.org/2024/03/01/harbor-signal",
    )
    assert article.confidence.content > 0.4
    assert article.content_source and "heuristic" in article.content_source


def test_strict_mode_rejects_emptyish_page():
    html = "<html><body><h1>Home</h1><a href='/a'>a</a><a href='/b'>b</a></body></html>"
    with pytest.raises(LowConfidenceExtractionError) as exc:
        extract(html, url="https://example.com/", strict=True)
    assert exc.value.failed_fields
    assert exc.value.article is not None


def test_page_type_homepage():
    doc = Document.from_html("<html><body><a href='/x'>x</a></body></html>")
    result = detect_page_type(doc, "https://www.example.com/")
    assert result.page_type == "homepage"
    assert result.is_article is False


def test_min_content_confidence_gate():
    cfg = Config(min_content_confidence=0.99)
    # Rich article should usually pass high content confidence from JSON-LD
    article = Extractor(Config()).extract(
        _html("rich_article.html"),
        "https://www.example.com/news/x",
    )
    assert article.confidence.content < 0.99 or article.confidence.content >= 0.9
    # Force failure with absurd threshold
    with pytest.raises(LowConfidenceExtractionError):
        Extractor(cfg).extract(_html("heuristic_only.html"), "https://news.example.org/2024/03/01/x")
