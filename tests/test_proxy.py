"""Proxy normalization / rotation tests."""

import pytest

from newsfetch.client.proxy import ProxyRotator, normalize_proxies
from newsfetch.config import Config


def test_normalize_single_proxy_url():
    maps = normalize_proxies(proxy="http://user:pass@127.0.0.1:8080")
    assert maps == [
        {
            "http": "http://user:pass@127.0.0.1:8080",
            "https": "http://user:pass@127.0.0.1:8080",
        }
    ]


def test_normalize_proxy_dict():
    maps = normalize_proxies(proxies={"http": "http://a:1", "https": "http://a:1"})
    assert len(maps) == 1
    assert maps[0]["http"] == "http://a:1"


def test_normalize_proxy_pool():
    maps = normalize_proxies(proxies=["http://p1:1", "http://p2:2"])
    assert len(maps) == 2
    assert maps[0]["https"] == "http://p1:1"
    assert maps[1]["https"] == "http://p2:2"


def test_proxy_and_proxies_mutex():
    with pytest.raises(ValueError):
        normalize_proxies(proxy="http://a", proxies="http://b")


def test_rotator_round_robin():
    rotator = ProxyRotator(normalize_proxies(proxies=["http://p1", "http://p2"]))
    assert rotator.next()["http"] == "http://p1"
    assert rotator.next()["http"] == "http://p2"
    assert rotator.next()["http"] == "http://p1"


def test_config_proxy_pool():
    cfg = Config(proxies=["http://a:1", "http://b:2"], rotate_proxies=True)
    assert len(cfg.proxy_pool()) == 2
    assert cfg.proxy_rotator().pool_size == 2


def test_fetch_kwargs_accept_proxy(monkeypatch):
    """Ensure proxy kwargs flow into Config without network I/O."""
    from newsfetch import api

    seen = {}

    class FakeFetcher:
        def __init__(self, config):
            seen["proxy"] = config.proxy
            seen["proxies"] = config.proxies

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def fetch(self, url, html=None):
            from newsfetch.models import Article

            return Article(url=url, title="t", text="hello world " * 20)

    monkeypatch.setattr(api, "NewsFetcher", FakeFetcher)
    article = api.fetch("https://example.com/a", proxy="http://127.0.0.1:8888")
    assert article.title == "t"
    assert seen["proxy"] == "http://127.0.0.1:8888"
