"""Package smoke tests."""

from newsfetch import Article, NewsFetcher, __version__, fetch


def test_version():
    assert __version__ == "1.0.0"


def test_public_exports():
    assert callable(fetch)
    assert NewsFetcher is not None
    assert Article is not None
