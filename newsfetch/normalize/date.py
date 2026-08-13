"""Date parsing and normalization."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from dateutil import parser as date_parser

_URL_DATE_RE = re.compile(
    r"(?P<y>20\d{2})[-/](?P<m>0?[1-9]|1[0-2])[-/](?P<d>0?[1-9]|[12]\d|3[01])"
)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        dt = date_parser.parse(value, fuzzy=True)
    except (ValueError, OverflowError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def date_from_url(url: str) -> datetime | None:
    match = _URL_DATE_RE.search(url)
    if not match:
        return None
    try:
        return datetime(
            int(match.group("y")),
            int(match.group("m")),
            int(match.group("d")),
            tzinfo=timezone.utc,
        )
    except ValueError:
        return None
