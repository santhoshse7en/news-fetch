"""Date parsing and normalization."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from dateutil import parser as date_parser

_URL_DATE_RE = re.compile(
    r"(?P<y>20\d{2})[-/](?P<m>0?[1-9]|1[0-2])[-/](?P<d>0?[1-9]|[12]\d|3[01])"
)


# Two distinct defaults: any calendar field dateutil fills from the default differs between
# the two parses, which means the input never contained it
_DEFAULT_A = datetime(1904, 1, 1)
_DEFAULT_B = datetime(1905, 2, 2)


def parse_date(value: str | None) -> datetime | None:
    """Parse a date string; reject inputs missing year, month, or day (no guessing from today)."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        dt = date_parser.parse(value, fuzzy=True, default=_DEFAULT_A)
        check = date_parser.parse(value, fuzzy=True, default=_DEFAULT_B)
    except (ValueError, OverflowError, TypeError):
        return None
    if dt.date() != check.date():
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
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
            tzinfo=UTC,
        )
    except ValueError:
        return None
