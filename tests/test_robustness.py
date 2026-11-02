"""Size limits, RFC 9309 robots.txt, hardened XML, and discovery via HttpClient (1.1)."""

import asyncio
import gzip
import importlib
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from newsfetch import Config, NewsFetcher
from newsfetch.client.http import HttpClient
from newsfetch.client.robots import RobotsCache, RobotsRules, product_token
from newsfetch.discover import SiteDiscoverer, discover
from newsfetch.errors import FetchError

UA = "news-fetch/1.1 (+https://github.com/santhoshse7en/news-fetch)"


@pytest.fixture
def server():
    """Local HTTP server: set ``srv.routes[path] = (status, headers, body)``."""
    routes: dict[str, tuple[int, dict[str, str], bytes]] = {}
    seen: list[tuple[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("User-Agent", "")))
            status, headers, body = routes.get(self.path, (404, {}, b"not found"))
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
    httpd.base = f"http://127.0.0.1:{httpd.server_port}"
    httpd.routes = routes
    httpd.seen = seen
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def _client(**kwargs) -> HttpClient:
    return HttpClient(Config(retries=0, user_agent=UA, **kwargs))


# --- size limit -------------------------------------------------------------------------


def test_body_over_max_bytes_raises(server):
    server.routes["/big"] = (200, {}, b"x" * 5000)  # no Content-Length: enforced while streaming
    with pytest.raises(FetchError, match="too large"):
        _client(max_bytes=1000).get(server.base + "/big")


def test_declared_content_length_over_limit_raises(server):
    server.routes["/big"] = (200, {"Content-Length": "5000"}, b"x" * 5000)
    with pytest.raises(FetchError, match="5000 bytes"):
        _client(max_bytes=1000).get(server.base + "/big")


def test_gzip_bomb_limited_after_decompression(server):
    bomb = gzip.compress(b"\0" * (5 * 1024 * 1024))  # ~5 KB on the wire, 5 MiB decoded
    server.routes["/bomb"] = (200, {"Content-Encoding": "gzip", "Content-Length": str(len(bomb))}, bomb)
    with pytest.raises(FetchError, match="too large"):
        _client(max_bytes=1024 * 1024).get(server.base + "/bomb")


def test_truncate_and_unlimited(server):
    server.routes["/big"] = (200, {}, b"x" * 5000)
    assert len(_client(max_bytes=1000).get(server.base + "/big", truncate=True).content) == 1000
    assert len(_client(max_bytes=1000).get(server.base + "/big", max_bytes=0).content) == 5000
    assert len(_client().get(server.base + "/big").content) == 5000  # default 10 MiB


def test_async_fetch_respects_max_bytes(server):
    pytest.importorskip("httpx")
    from newsfetch import fetch_async

    server.routes["/big"] = (200, {}, b"<html>" + b"x" * 5000 + b"</html>")
    with pytest.raises(FetchError, match="too large"):
        asyncio.run(fetch_async(server.base + "/big", max_bytes=1000))


# --- robots.txt (RFC 9309) --------------------------------------------------------------


def test_product_token():
    assert product_token(UA) == "news-fetch"
    assert product_token("Googlebot/2.1") == "googlebot"


def test_robots_wildcards_anchor_and_longest_match():
    rules = RobotsRules.parse(
        """
        User-agent: *
        Disallow: /private
        Allow: /private/public
        Disallow: /*.pdf$
        Disallow: /search?*q=
        Allow: /page
        Disallow: /page
        """
    )
    url = "https://example.com"
    assert rules.allowed(UA, url + "/news/story")
    assert not rules.allowed(UA, url + "/private/x")
    assert rules.allowed(UA, url + "/private/public/x")  # longer allow beats shorter disallow
    assert not rules.allowed(UA, url + "/files/report.pdf")
    assert rules.allowed(UA, url + "/files/report.pdf?download=1")  # $ anchors the end
    assert not rules.allowed(UA, url + "/search?lang=en&q=x")
    assert rules.allowed(UA, url + "/page")  # equal length: allow wins
    assert rules.allowed(UA, url + "/robots.txt")


def test_robots_group_selection():
    rules = RobotsRules.parse(
        """
        Disallow: /ignored-before-any-user-agent

        User-agent: *
        Disallow: /

        User-agent: News-Fetch
        Disallow: /a

        User-agent: other
        User-agent: news-fetch
        Disallow: /b
        """
    )
    url = "https://example.com"
    # Groups naming our product token are combined (case-insensitive); "*" is not used
    assert rules.allowed(UA, url + "/news")
    assert not rules.allowed(UA, url + "/a")
    assert not rules.allowed(UA, url + "/b")
    assert not rules.allowed("SomeBot/1.0", url + "/news")  # falls back to "*"


def test_robots_percent_encoding_normalized():
    rules = RobotsRules.parse("User-agent: *\nDisallow: /caf%C3%A9\n")
    assert not rules.allowed(UA, "https://example.com/café/x")
    assert not rules.allowed(UA, "https://example.com/caf%c3%a9/x")


@pytest.mark.parametrize(
    ("status", "allowed", "reason"),
    [(404, True, "unavailable"), (403, True, "unavailable"), (503, False, "unreachable"), (429, False, "unreachable")],
)
def test_robots_status_handling(server, status, allowed, reason):
    server.routes["/robots.txt"] = (status, {}, b"User-agent: *\nDisallow: /\n")
    decision = RobotsCache(UA, client=_client()).check(server.base + "/news")
    assert decision.allowed is allowed
    assert reason in decision.reason


def test_robots_network_error_disallows():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()  # nothing listening → connection refused
    decision = RobotsCache(UA, client=_client(timeout=2)).check(f"http://127.0.0.1:{port}/a")
    assert not decision.allowed
    assert "network error" in decision.reason


def test_fetcher_respect_robots_uses_client_and_reports_reason(server):
    server.routes["/robots.txt"] = (200, {}, b"User-agent: news-fetch\nDisallow: /blocked\n")
    fetcher = NewsFetcher(Config(respect_robots=True, retries=0, user_agent=UA))
    with pytest.raises(FetchError, match="disallowed by robots.txt"):
        fetcher.fetch(server.base + "/blocked/story")
    assert ("/robots.txt", UA) in server.seen  # fetched with the configured user agent
    fetcher.close()


# --- discovery + hardened XML -----------------------------------------------------------


def _sitemap(*urls: str) -> bytes:
    locs = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'.encode()


def test_discover_uses_configured_client(server):
    server.routes["/robots.txt"] = (200, {}, f"Sitemap: {server.base}/news-sitemap.xml\n".encode())
    server.routes["/news-sitemap.xml"] = (200, {}, _sitemap("https://example.com/a", "https://example.com/b"))
    with NewsFetcher(Config(retries=0, user_agent=UA)) as fetcher:
        items = fetcher.discover(server.base)
    assert [i["url"] for i in items] == ["https://example.com/a", "https://example.com/b"]
    user_agents = {ua for path, ua in server.seen}
    assert user_agents == {UA}  # previously python-requests/x.y


def test_discover_skips_oversized_feed(server, monkeypatch):
    server.routes["/robots.txt"] = (200, {}, f"Sitemap: {server.base}/news-sitemap.xml\n".encode())
    server.routes["/news-sitemap.xml"] = (200, {}, _sitemap(*[f"https://example.com/{i}" for i in range(200)]))
    # `newsfetch.discover` the attribute is the function; fetch the module itself
    monkeypatch.setattr(importlib.import_module("newsfetch.discover"), "_MAX_FEED_BYTES", 500)
    assert discover(server.base, client=_client()) == []


def test_sitemap_entities_not_expanded(server, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET")
    body = (
        f'<?xml version="1.0"?><!DOCTYPE urlset [<!ENTITY int "https://evil.example/injected">'
        f'<!ENTITY ext SYSTEM "file://{secret}">]>'
        "<urlset><url><loc>&int;</loc></url><url><loc>&ext;</loc></url>"
        "<url><loc>https://example.com/ok</loc></url></urlset>"
    ).encode()
    server.routes["/robots.txt"] = (200, {}, f"Sitemap: {server.base}/news-sitemap.xml\n".encode())
    server.routes["/news-sitemap.xml"] = (200, {}, body)
    urls = SiteDiscoverer(server.base, client=_client()).urls
    assert urls == ["https://example.com/ok"]
    assert not any("TOP-SECRET" in u or "evil" in u for u in urls)


def test_sitemap_billion_laughs_is_inert(server):
    entities = '<!ENTITY a0 "lol">' + "".join(f'<!ENTITY a{i} "{f"&a{i - 1};" * 10}">' for i in range(1, 10))
    body = (
        f'<?xml version="1.0"?><!DOCTYPE urlset [{entities}]>'
        "<urlset><url><loc>https://example.com/&a9;</loc></url></urlset>"
    ).encode()
    server.routes["/robots.txt"] = (200, {}, f"Sitemap: {server.base}/news-sitemap.xml\n".encode())
    server.routes["/news-sitemap.xml"] = (200, {}, body)
    urls = SiteDiscoverer(server.base, client=_client()).urls
    assert all(len(u) < 100 for u in urls)  # 10**9 "lol"s were never expanded
