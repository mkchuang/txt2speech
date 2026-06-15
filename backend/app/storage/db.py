import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS syntheses (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    text_excerpt TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'text',
    voice TEXT NOT NULL,
    pacing TEXT,
    style TEXT,
    accent TEXT,
    format TEXT NOT NULL,
    audio_path TEXT NOT NULL,
    duration_ms INTEGER,
    status TEXT NOT NULL
)
"""


class Database:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = settings.data_dir_path / "app.sqlite"
        self.db_path = str(db_path) if isinstance(db_path, Path) else db_path

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(CREATE_TABLE_SQL)
        self.conn.commit()
        logger.info("Database schema initialized (path=%s)", self.db_path)

    def create(
        self,
        text_excerpt: str,
        char_count: int,
        voice: str,
        format: str,
        audio_path: str,
        status: str,
        source: str = "text",
        pacing: str | None = None,
        style: str | None = None,
        accent: str | None = None,
        duration_ms: int | None = None,
    ) -> dict:
        record_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        self.conn.execute(
            """INSERT INTO syntheses
               (id, created_at, text_excerpt, char_count, source, voice,
                pacing, style, accent, format, audio_path, duration_ms, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record_id,
                created_at,
                text_excerpt,
                char_count,
                source,
                voice,
                pacing,
                style,
                accent,
                format,
                audio_path,
                duration_ms,
                status,
            ),
        )
        self.conn.commit()
        logger.info(
            "Created synthesis record id=%s status=%s", record_id, status
        )
        record = self.get(record_id)
        if record is None:
            raise RuntimeError(
                f"Created synthesis record cannot be loaded: {record_id}"
            )
        return record

    def list_items(self, limit: int = 50, offset: int = 0) -> dict:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        cursor = self.conn.execute("SELECT COUNT(*) FROM syntheses")
        total = cursor.fetchone()[0]

        cursor = self.conn.execute(
            "SELECT * FROM syntheses ORDER BY created_at DESC, rowid DESC "
            "LIMIT ? OFFSET ?",
            (limit, offset),
        )
        items = [dict(row) for row in cursor.fetchall()]

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    def get(self, item_id: str) -> dict | None:
        cursor = self.conn.execute(
            "SELECT * FROM syntheses WHERE id = ?", (item_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete(self, item_id: str) -> bool:
        cursor = self.conn.execute(
            "DELETE FROM syntheses WHERE id = ?", (item_id,)
        )
        self.conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted synthesis record id=%s", item_id)
        return deleted

    def close(self) -> None:
        self.conn.close()


_default_db: Database | None = None


def get_database() -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db
