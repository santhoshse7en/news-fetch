"""Optional SQLite response/article cache (stdlib only)."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path


class DiskCache:
    """Simple URL → HTML disk cache backed by SQLite."""

    def __init__(self, path: str | Path = ".news-fetch-cache.sqlite", *, ttl: int = 86400) -> None:
        self.path = Path(path)
        self.ttl = ttl
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                key TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                content BLOB NOT NULL,
                fetched_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get(self, url: str) -> bytes | None:
        key = self._key(url)
        row = self._conn.execute(
            "SELECT content, fetched_at FROM pages WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        content, fetched_at = row
        if self.ttl > 0 and (time.time() - fetched_at) > self.ttl:
            self._conn.execute("DELETE FROM pages WHERE key = ?", (key,))
            self._conn.commit()
            return None
        return content

    def set(self, url: str, content: bytes) -> None:
        key = self._key(url)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO pages (key, url, content, fetched_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, url, content, time.time()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
