"""SQLite storage backend for LogSweeper."""

import sqlite3
import logging
from contextlib import contextmanager

from .models import Event

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    hostname TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    raw TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
"""


class Database:
    """SQLite database wrapper."""

    def __init__(self, db_path: str = "logsweeper.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript(SCHEMA)
        logger.info("Database initialized at %s", self.db_path)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def insert_event(self, event: Event) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO events (timestamp, source, hostname, category, message, raw) VALUES (?, ?, ?, ?, ?, ?)",
                (event.timestamp, event.source, event.hostname, event.category, event.message, event.raw),
            )
            return cursor.lastrowid

    def insert_events(self, events: list[Event]) -> int:
        with self._connect() as conn:
            cursor = conn.executemany(
                "INSERT INTO events (timestamp, source, hostname, category, message, raw) VALUES (?, ?, ?, ?, ?, ?)",
                [(e.timestamp, e.source, e.hostname, e.category, e.message, e.raw) for e in events],
            )
            return cursor.rowcount

    def query_events(
        self,
        source: str | None = None,
        category: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        query = "SELECT * FROM events WHERE 1=1"
        params: list = []

        if source:
            query += " AND source = ?"
            params.append(source)
        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (message LIKE ? OR raw LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def count_events(self, source: str | None = None, category: str | None = None, search: str | None = None) -> int:
        query = "SELECT COUNT(*) as cnt FROM events WHERE 1=1"
        params: list = []
        if source:
            query += " AND source = ?"
            params.append(source)
        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (message LIKE ? OR raw LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return row["cnt"]

    def get_event(self, event_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
            return dict(row) if row else None

    def get_sources(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT source FROM events ORDER BY source").fetchall()
            return [row["source"] for row in rows]

    def get_categories(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT category FROM events ORDER BY category").fetchall()
            return [row["category"] for row in rows]
