from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "tutor.db"


class TutorDatabase:
    """SQLite store for course, document, and chat records.

    ChromaDB remains responsible for vector embeddings; this database owns the
    relational application records and their foreign-key relationships.
    """

    def __init__(self, path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS course (
                    course_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS document (
                    document_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL DEFAULT '',
                    processed_path TEXT NOT NULL DEFAULT '',
                    upload_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    FOREIGN KEY (course_id) REFERENCES course(course_id)
                );

                CREATE TABLE IF NOT EXISTS conversation (
                    conversation_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (course_id) REFERENCES course(course_id)
                );

                CREATE TABLE IF NOT EXISTS message (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversation(conversation_id)
                );

                CREATE INDEX IF NOT EXISTS idx_document_course ON document(course_id);
                CREATE INDEX IF NOT EXISTS idx_conversation_course ON conversation(course_id);
                CREATE INDEX IF NOT EXISTS idx_message_conversation ON message(conversation_id, timestamp);
                """
            )
            existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(document)")}
            if "stored_filename" not in existing_columns:
                connection.execute("ALTER TABLE document ADD COLUMN stored_filename TEXT NOT NULL DEFAULT ''")
            if "processed_path" not in existing_columns:
                connection.execute("ALTER TABLE document ADD COLUMN processed_path TEXT NOT NULL DEFAULT ''")
            schema = connection.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'document'").fetchone()[0] or ""
            if "CHECK (status IN ('indexing', 'indexed', 'failed'))" in schema:
                connection.executescript(
                    """
                    CREATE TABLE document_replacement (
                        document_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        stored_filename TEXT NOT NULL DEFAULT '',
                        processed_path TEXT NOT NULL DEFAULT '',
                        upload_date TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        FOREIGN KEY (course_id) REFERENCES course(course_id)
                    );
                    INSERT INTO document_replacement
                    SELECT document_id, course_id, filename, stored_filename, processed_path, upload_date,
                        CASE status WHEN 'indexing' THEN 'processing' WHEN 'indexed' THEN 'completed' ELSE status END
                    FROM document;
                    DROP TABLE document;
                    ALTER TABLE document_replacement RENAME TO document;
                    CREATE INDEX IF NOT EXISTS idx_document_course ON document(course_id);
                    """
                )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_course(self, course_id: str, name: str, description: str = "") -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO course (course_id, name, description) VALUES (?, ?, ?)
                ON CONFLICT(course_id) DO UPDATE SET name = excluded.name, description = excluded.description
                """,
                (course_id, name, description),
            )

    def ensure_course(self, course_id: str) -> None:
        """Create a minimal course record until course details are supplied."""
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO course (course_id, name, description) VALUES (?, ?, '')",
                (course_id, course_id),
            )

    def list_courses(self) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM course ORDER BY rowid").fetchall()
        return [dict(row) for row in rows]

    def create_document(self, document_id: str, course_id: str, filename: str, stored_filename: str = "", processed_path: str = "") -> None:
        self.ensure_course(course_id)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO document (document_id, course_id, filename, stored_filename, processed_path, upload_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                (document_id, course_id, filename, stored_filename, processed_path, self._now()),
            )

    def set_document_status(self, document_id: str, status: str) -> None:
        if status not in {"pending", "processing", "completed", "failed", "indexing", "indexed"}:
            raise ValueError("Unsupported document status.")
        with self._connection() as connection:
            connection.execute(
                "UPDATE document SET status = ? WHERE document_id = ?",
                (status, document_id),
            )

    def create_conversation(self, course_id: str, conversation_id: str | None = None) -> str:
        self.ensure_course(course_id)
        conversation_id = conversation_id or uuid4().hex
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO conversation (conversation_id, course_id, created_at) VALUES (?, ?, ?)",
                (conversation_id, course_id, self._now()),
            )
        return conversation_id

    def get_or_create_conversation(self, course_id: str, conversation_id: str | None = None) -> str:
        if not conversation_id:
            return self.create_conversation(course_id)

        with self._connection() as connection:
            row = connection.execute(
                "SELECT course_id FROM conversation WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        if row is None:
            return self.create_conversation(course_id, conversation_id)
        if row["course_id"] != course_id:
            raise ValueError("Conversation belongs to a different course.")
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        if role not in {"user", "assistant"}:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        message_id = uuid4().hex
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO message (message_id, conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message_id, conversation_id, role, content, self._now()),
            )
        return message_id

    def get_document(self, document_id: str) -> dict[str, str] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM document WHERE document_id = ?", (document_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self, course_id: str) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM document WHERE course_id = ? ORDER BY upload_date DESC", (course_id,)).fetchall()
        return [dict(row) for row in rows]

    def rename_document(self, document_id: str, course_id: str, filename: str) -> bool:
        with self._connection() as connection:
            result = connection.execute("UPDATE document SET filename = ? WHERE document_id = ? AND course_id = ?", (filename, document_id, course_id))
        return result.rowcount == 1

    def delete_document(self, document_id: str, course_id: str) -> dict[str, str] | None:
        document = self.get_document(document_id)
        if not document or document["course_id"] != course_id:
            return None
        with self._connection() as connection:
            connection.execute("DELETE FROM document WHERE document_id = ?", (document_id,))
        return document

    def get_messages(self, conversation_id: str) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM message WHERE conversation_id = ? ORDER BY timestamp",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]


_database: TutorDatabase | None = None


def get_database() -> TutorDatabase:
    global _database
    if _database is None:
        _database = TutorDatabase()
    return _database
