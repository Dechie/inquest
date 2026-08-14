"""SQLite database bootstrap."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from codeanalyzer.persistence.schema import MIGRATION_V2_SQL, SCHEMA_SQL


class Database:
    """Thin SQLite wrapper that applies the analysis schema."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def initialize(self) -> None:
        conn = self.connect()
        conn.executescript(SCHEMA_SQL)
        applied = {
            row[0]
            for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }
        migrations: dict[int, str] = {2: MIGRATION_V2_SQL}
        for version in sorted(migrations):
            if version in applied:
                continue
            conn.executescript(migrations[version])
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, datetime.now(UTC).isoformat()),
            )
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Database:
        self.initialize()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
