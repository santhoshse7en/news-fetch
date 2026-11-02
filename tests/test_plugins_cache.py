"""Plugin strategy and cache tests."""

from newsfetch import CallableStrategy, Config, NewsFetcher
from newsfetch.client.cache import DiskCache
from newsfetch.strategies.base import Candidate


def test_register_strategy_overrides_title():
    html = (
        "<html><body><h1>Original</h1>"
        "<p>Body text with enough words to pass filters for extraction heuristics here.</p>"
        "<p>Second paragraph keeps the article body candidate alive for ranking.</p>"
        "</body></html>"
    )

    def plugin(doc):
        return {"title": [Candidate("Plugin Title Win", "plugin.demo", 0.99)]}

    fetcher = NewsFetcher(Config())
    fetcher.register_strategy(CallableStrategy("demo", plugin))
    article = fetcher.fetch("https://example.com/a", html=html)
    assert article.title == "Plugin Title Win"


def test_disk_cache(tmp_path):
    path = tmp_path / "c.sqlite"
    cache = DiskCache(path, ttl=60)
    cache.set("https://example.com/x", b"<html>hi</html>")
    assert cache.get("https://example.com/x") == b"<html>hi</html>"
    cache.close()


def test_disk_cache_concurrent_threads(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    cache = DiskCache(tmp_path / "c.sqlite", ttl=60)

    def worker(i):
        for j in range(50):
            url = f"https://example.com/{i}/{j}"
            cache.set(url, b"<html>x</html>")
            assert cache.get(url) == b"<html>x</html>"

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(worker, range(16)))  # re-raises any sqlite InterfaceError
    cache.close()
