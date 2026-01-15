from __future__ import annotations

import sqlite3
from pathlib import Path


class ArticleStateStore:
    """Tiny SQLite-backed state store.

    Goals:
    - Persist which detail URLs have been successfully scraped (incremental runs).
    - Persist whether a full archives crawl has ever completed (safe early-stop).
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def open(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._ensure_schema()

    def close(self) -> None:
        if self._conn is None:
            return
        self._conn.close()
        self._conn = None

    def _ensure_schema(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                title TEXT,
                tag TEXT,
                published_time TEXT,
                modified_time TEXT,
                first_seen TEXT,
                last_seen TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        self._conn.commit()

    def load_seen_urls(self) -> set[str]:
        assert self._conn is not None
        rows = self._conn.execute("SELECT url FROM articles").fetchall()
        return {r[0] for r in rows}

    def upsert_article(
        self,
        *,
        url: str,
        title: str | None,
        tag: str | None,
        published_time: str | None,
        modified_time: str | None,
        seen_at: str,
    ) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO articles (url, title, tag, published_time, modified_time, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                tag = excluded.tag,
                published_time = excluded.published_time,
                modified_time = excluded.modified_time,
                last_seen = excluded.last_seen
            """,
            (url, title, tag, published_time, modified_time, seen_at, seen_at),
        )
        self._conn.commit()

    def get_meta(self, key: str) -> str | None:
        assert self._conn is not None
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return row[0]

    def set_meta(self, key: str, value: str) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO meta (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self._conn.commit()

    def is_full_crawl_completed(self) -> bool:
        return self.get_meta("full_crawl_completed") == "1"

    def mark_full_crawl_completed(self) -> None:
        self.set_meta("full_crawl_completed", "1")
