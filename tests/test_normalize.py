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
