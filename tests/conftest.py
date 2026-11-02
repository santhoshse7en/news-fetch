from __future__ import annotations

# pytest configuration lives in pyproject.toml
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


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
