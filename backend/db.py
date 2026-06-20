import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import config
from models import Agent, Chat, Message


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

    def _row_to_agent(self, row: sqlite3.Row) -> Agent:
        return Agent(
            id=row["id"],
            name=row["name"],
            avatar=row["avatar"],
            title=row["title"],
            system_message=row["system_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def init_db(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                avatar TEXT NOT NULL DEFAULT '🤖',
                title TEXT NOT NULL DEFAULT '',
                system_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
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
        try:
            conn.execute("ALTER TABLE chats ADD COLUMN agent_id TEXT")
        except Exception:
            pass
        now = datetime.now(timezone.utc).isoformat()
        defaults = [
            ("mentor", "Marcus", "🧙‍♂️", "Wise Mentor",
             "You are Marcus, a wise and experienced mentor. You speak with calm authority and ancient wisdom. You guide the user through challenges with parables and thoughtful advice. You are patient, kind, but honest. Your responses are measured and profound. Pay attention to the user's emotional state. If they seem sad, offer gentle wisdom and perspective. If angry, give them space to vent before guiding. If anxious, be grounding and reassuring. If happy, celebrate with them and encourage their growth."),
            ("friend", "Sophie", "👩‍🦰", "Supportive Friend",
             "You are Sophie, a warm and supportive friend. You are caring, empathetic, and always there to listen. You use casual, friendly language and sometimes humor. You are the kind of friend who knows when to offer advice and when to just be present. You care deeply about the user wellbeing. Pay attention to the user's emotional state. If they seem sad, respond with warmth and gentle validation. If angry, acknowledge their feelings and give them space. If anxious, be calming and reassuring. If happy, share their joy and energy."),
        ]
        for aid, name, avatar, title, sysmsg in defaults:
            conn.execute(
                "INSERT OR REPLACE INTO agents (id, name, avatar, title, system_message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (aid, name, avatar, title, sysmsg, now),
            )
        conn.commit()
        if conn is not self._mem_conn:
            conn.close()

    def list_agents(self) -> list[Agent]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM agents ORDER BY created_at ASC").fetchall()
        if conn is not self._mem_conn:
            conn.close()
        return [self._row_to_agent(r) for r in rows]

    def get_agent(self, agent_id: str) -> Agent | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_agent(row) if row else None

    def create_agent(self, name: str, avatar: str, title: str, system_message: str) -> Agent:
        conn = self._connect()
        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO agents (id, name, avatar, title, system_message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (agent_id, name, avatar, title, system_message, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if conn is not self._mem_conn:
            conn.close()
        return self._row_to_agent(row)

    def delete_agent(self, agent_id: str) -> bool:
        conn = self._connect()
        cursor = conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()
        affected = cursor.rowcount
        if conn is not self._mem_conn:
            conn.close()
        return affected > 0

    def _row_to_chat(self, row: sqlite3.Row) -> Chat:
        return Chat(
            id=row["id"],
            agent_id=row["agent_id"],
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

    def create_chat(self, title: str, system_message: str = "", agent_id: str | None = None) -> Chat:
        conn = self._connect()
        chat_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO chats (id, agent_id, title, system_message, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, agent_id, title, system_message, now, now),
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
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
        rows.reverse()
        if conn is not self._mem_conn:
            conn.close()
        return [self._row_to_message(r) for r in rows]


db = Database()
