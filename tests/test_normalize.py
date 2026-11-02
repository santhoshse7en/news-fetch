"""Tests for date and URL helpers."""

from newsfetch.normalize.date import date_from_url, parse_date
from newsfetch.normalize.url import absolutize, domain_from_url


def test_parse_date_iso():
    dt = parse_date("2024-06-15T10:30:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 6


def test_date_from_url():
    dt = date_from_url("https://example.com/2023/07/04/story")
    assert dt is not None
    assert (dt.year, dt.month, dt.day) == (2023, 7, 4)


def test_absolutize_and_domain():
    assert absolutize("https://ex.com/a/", "/img/x.jpg") == "https://ex.com/img/x.jpg"
    assert domain_from_url("https://www.ex.com/a") == "ex.com"


def test_parse_date_rejects_partial_or_relative_dates():
    # dateutil(fuzzy) used to fill missing fields from "today" and fabricate dates
    for value in ("Updated 3 hours ago", "Ref 12", "May 2", "Posted by staff on Tuesday"):
        assert parse_date(value) is None, value


def test_parse_date_keeps_complete_dates():
    dt = parse_date("Published Tuesday, 5 March 2024 at 10:15")
    assert dt is not None
    assert (dt.year, dt.month, dt.day) == (2024, 3, 5)
    assert parse_date("Mar 5, 2024") is not None


def test_keywords_non_latin_text():
    from newsfetch.nlp import extract_keywords

    keywords = extract_keywords("Москва новости Москва правительство новости Москва")
    assert keywords[0] == "москва"
    assert "новости" in keywords


def test_normalize_language_primary_subtag():
    from newsfetch.detect.language import normalize_language

    assert normalize_language("en-GB") == "en"
    assert normalize_language("pt_BR") == "pt"
    assert normalize_language("fil") == "fil"  # was truncated to "fi" (Finnish)
    assert normalize_language("zh-Hant-TW") == "zh"
    assert normalize_language("de, en") == "de"
    assert normalize_language("  ") is None
