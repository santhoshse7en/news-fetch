"""URL normalization."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "vero_id",
    "ref",
    "ref_src",
    "ref_url",
}


def absolutize(base: str, url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if not url or url.startswith(("data:", "javascript:", "mailto:")):
        return None
    return urljoin(base, url)


def canonicalize(url: str, *, strip_tracking: bool = True) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    query = parts.query
    if strip_tracking and query:
        kept = [
            (k, v)
            for k, v in parse_qsl(query, keep_blank_values=True)
            if k.lower() not in _TRACKING_PARAMS
        ]
        query = urlencode(kept)
    # Drop fragment
    return urlunsplit((scheme, netloc, path, query, ""))


def domain_from_url(url: str) -> str | None:
    host = urlsplit(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None
