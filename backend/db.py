import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import config
from models import Chat, Message


class Database:
    def __init__(self, db_path: str = config.db_path):
        self.db_path = db_path
        self._mem_conn: Optional[sqlite3.Connection] = None
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
                self._mem_conn.execute("PRAGMA foreign_keys=ON")
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                system_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
        """)
        conn.commit()
        if conn is not self._mem_conn:
            conn.close()

    def _row_to_chat(self, row: sqlite3.Row) -> Chat:
        return Chat(
            id=row["id"],
            title=row["title"],
            system_message=row["system_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_message(self, row: sqlite3.Row) -> Message:
        return Message(
            id=row["id"],
            chat_id=row["chat_id"],
            role=row["role"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def create_chat(self, title: str, system_message: str = "") -> Chat:
        conn = self._connect()
        chat_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO chats (id, title, system_message, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, title, system_message, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_chat(row)

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        conn = self._connect()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_chat(row) if row else None

    def list_chats(self) -> list[Chat]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM chats ORDER BY updated_at DESC").fetchall()
        if conn is not self._mem_conn:
            conn.close()
        return [self._row_to_chat(r) for r in rows]

    def update_chat(self, chat_id: str, title: Optional[str] = None, system_message: Optional[str] = None) -> Optional[Chat]:
        conn = self._connect()
        now = datetime.now(timezone.utc).isoformat()
        updates = ["updated_at = ?"]
        params = [now]
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if system_message is not None:
            updates.append("system_message = ?")
            params.append(system_message)
        params.append(chat_id)
        conn.execute(f"UPDATE chats SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_chat(row) if row else None

    def delete_chat(self, chat_id: str) -> bool:
        conn = self._connect()
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        affected = cursor.rowcount
        if conn is not self._mem_conn:
            conn.close()
        return affected > 0

    def reset_chat(self, chat_id: str) -> bool:
        conn = self._connect()
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.commit()
        if conn is not self._mem_conn:
            conn.close()
        return True

    def add_message(self, chat_id: str, role: str, content: str) -> Message:
        conn = self._connect()
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO messages (id, chat_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, chat_id, role, content, now),
        )
        conn.execute(
            "UPDATE chats SET updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), chat_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_message(row)

    def get_messages(self, chat_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        ).fetchall()
        if conn is not self._mem_conn:
            conn.close()
        return [self._row_to_message(r) for r in rows]


db = Database()
