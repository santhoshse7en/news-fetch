"""HTTP client package."""

from newsfetch.client.cache import DiskCache
from newsfetch.client.http import HttpClient, Response
from newsfetch.client.proxy import ProxyMap, ProxyRotator, normalize_proxies

__all__ = [
    "DiskCache",
    "HttpClient",
    "ProxyMap",
    "ProxyRotator",
    "Response",
    "normalize_proxies",
]
