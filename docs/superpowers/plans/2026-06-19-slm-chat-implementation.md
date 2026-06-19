# SLM Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a chat application with per-chat graph memory, powered by `floxy/LFM2.5-Instruct:1.2b` via ollama.

**Architecture:** FastAPI backend with SQLite for message persistence and NetworkX per-chat graphs for long-term memory. React (Vite + TypeScript) frontend with SSE streaming. Three Docker services: ollama, backend, frontend.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, NetworkX, ollama, React 18+, TypeScript, Vite, nginx, Docker

## Global Constraints

- No content filtering for NSFW
- Model: `floxy/LFM2.5-Instruct:1.2b` via ollama
- Each chat has its own system message and its own NetworkX graph
- Graph memory uses entity extraction via the same ollama model
- SSE streaming for real-time responses
- Docker compose with 3 services
- Python >= 3.10, Node >= 18

---

### Task 1: Backend Foundation — Config, Models, Database

**Files:**
- Create: `backend/config.py`
- Create: `backend/models.py`
- Create: `backend/db.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_db.py`

**Interfaces:**
- Consumes: nothing (foundation task)
- Produces: `Config`, Pydantic models (`Chat`, `Message`, `CreateChat`, `UpdateChat`, `CreateMessage`, `ChatListResponse`, `MessageListResponse`, `GraphNode`, `GraphEdge`, `GraphData`), `Database` class with full CRUD

- [ ] **Step 1: Create directory structure and requirements.txt**

```bash
mkdir -p backend/routes backend/tests
```

```
# backend/requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
networkx==3.4.2
pydantic==2.10.4
pydantic-settings==2.7.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Create backend/config.py**

```python
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "floxy/LFM2.5-Instruct:1.2b"
    db_path: str = "data/slm-chat.db"
    graph_dir: str = "data/graphs"
    max_graph_nodes: int = 5000
    context_window: int = 4096

    class Config:
        env_prefix = "SLM_"


config = Config()
```

- [ ] **Step 3: Create backend/models.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Chat(BaseModel):
    id: str
    title: str
    system_message: str = ""
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    created_at: datetime


class CreateChat(BaseModel):
    title: str = "New Chat"
    system_message: str = ""


class UpdateChat(BaseModel):
    title: Optional[str] = None
    system_message: Optional[str] = None


class CreateMessage(BaseModel):
    content: str


class ChatListResponse(BaseModel):
    chats: list[Chat]


class MessageListResponse(BaseModel):
    messages: list[Message]


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
```

- [ ] **Step 4: Create backend/db.py**

```python
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
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
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
        conn.close()
        return self._row_to_chat(row)

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        conn = self._connect()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        conn.close()
        return self._row_to_chat(row) if row else None

    def list_chats(self) -> list[Chat]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM chats ORDER BY updated_at DESC").fetchall()
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
        conn.close()
        return self._row_to_chat(row) if row else None

    def delete_chat(self, chat_id: str) -> bool:
        conn = self._connect()
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def reset_chat(self, chat_id: str) -> bool:
        conn = self._connect()
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.commit()
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
        conn.close()
        return self._row_to_message(row)

    def get_messages(self, chat_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        ).fetchall()
        conn.close()
        return [self._row_to_message(r) for r in rows]


db = Database()
```

- [ ] **Step 5: Create backend/tests/__init__.py** (empty)

- [ ] **Step 6: Create backend/tests/test_db.py**

```python
import pytest
from db import Database


@pytest.fixture
def db():
    d = Database(":memory:")
    d.init_db()
    return d


def test_create_chat(db):
    chat = db.create_chat("Test Chat", "You are a friend.")
    assert chat.title == "Test Chat"
    assert chat.system_message == "You are a friend."
    assert chat.id is not None


def test_get_chat(db):
    created = db.create_chat("Test", "msg")
    found = db.get_chat(created.id)
    assert found is not None
    assert found.id == created.id


def test_get_chat_not_found(db):
    assert db.get_chat("nonexistent") is None


def test_list_chats(db):
    db.create_chat("A")
    db.create_chat("B")
    chats = db.list_chats()
    assert len(chats) == 2


def test_update_chat(db):
    chat = db.create_chat("Old")
    updated = db.update_chat(chat.id, title="New")
    assert updated.title == "New"


def test_delete_chat(db):
    chat = db.create_chat("Delete me")
    assert db.delete_chat(chat.id) is True
    assert db.get_chat(chat.id) is None


def test_add_message(db):
    chat = db.create_chat("Chat")
    msg = db.add_message(chat.id, "user", "Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.chat_id == chat.id


def test_get_messages(db):
    chat = db.create_chat("Chat")
    db.add_message(chat.id, "user", "Hi")
    db.add_message(chat.id, "assistant", "Hello!")
    msgs = db.get_messages(chat.id)
    assert len(msgs) == 2


def test_reset_chat(db):
    chat = db.create_chat("Chat")
    db.add_message(chat.id, "user", "Hi")
    db.reset_chat(chat.id)
    assert len(db.get_messages(chat.id)) == 0
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python -m pytest tests/test_db.py -v`
Expected: all tests PASS

---

### Task 2: Graph Memory Module

**Files:**
- Create: `backend/graph_memory.py`
- Create: `backend/tests/test_graph_memory.py`

**Interfaces:**
- Consumes: `config`, `models.GraphData/GraphNode/GraphEdge`
- Produces: `GraphMemory` class

- [ ] **Step 1: Create backend/graph_memory.py**

```python
import json
from pathlib import Path
from typing import Optional

import networkx as nx

from config import config
from models import GraphData, GraphEdge, GraphNode


class GraphMemory:
    def __init__(self, graph_dir: str = config.graph_dir):
        self.graph_dir = Path(graph_dir)
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self._graphs: dict[str, nx.DiGraph] = {}

    def _graph_path(self, chat_id: str) -> Path:
        return self.graph_dir / f"{chat_id}.json"

    def create_graph(self, chat_id: str) -> nx.DiGraph:
        g = nx.DiGraph()
        self._graphs[chat_id] = g
        self._save_graph(chat_id, g)
        return g

    def load_graph(self, chat_id: str) -> nx.DiGraph:
        if chat_id in self._graphs:
            return self._graphs[chat_id]
        path = self._graph_path(chat_id)
        if path.exists():
            data = json.loads(path.read_text())
            g = nx.node_link_graph(data, directed=True, edges="edges")
            self._graphs[chat_id] = g
            return g
        return self.create_graph(chat_id)

    def _save_graph(self, chat_id: str, g: nx.DiGraph):
        data = nx.node_link_data(g, edges="edges")
        self._graph_path(chat_id).write_text(json.dumps(data, indent=2))

    def add_triple(self, chat_id: str, subject: str, relation: str, obj: str, properties: Optional[dict] = None):
        g = self.load_graph(chat_id)
        if subject not in g:
            g.add_node(subject, label=subject, node_type="entity", count=0)
        if obj not in g:
            g.add_node(obj, label=obj, node_type="entity", count=0)
        if g.has_edge(subject, obj):
            g[subject][obj]["weight"] = g[subject][obj].get("weight", 1) + 1
            g[subject][obj]["relation"] = relation
            g[subject][obj]["count"] = g[subject][obj].get("count", 1) + 1
        else:
            g.add_edge(subject, obj, relation=relation, weight=1.0, count=1)
        g.nodes[subject]["count"] = g.nodes[subject].get("count", 0) + 1
        g.nodes[obj]["count"] = g.nodes[obj].get("count", 0) + 1
        if properties:
            g.nodes[subject].update(properties)
            g.nodes[obj].update(properties)
        self._save_graph(chat_id, g)

    def query_context(self, chat_id: str, entities: list[str], max_results: int = 10) -> str:
        g = self.load_graph(chat_id)
        context_parts = []
        seen = set()
        for entity in entities:
            if entity not in g:
                continue
            neighbors = list(g.successors(entity)) + list(g.predecessors(entity))
            for neighbor in neighbors[:max_results]:
                edge_data = g.get_edge_data(entity, neighbor) or g.get_edge_data(neighbor, entity)
                if edge_data and (entity, neighbor) not in seen:
                    seen.add((entity, neighbor))
                    rel = edge_data.get("relation", "related_to")
                    context_parts.append(f"{entity} --({rel})--> {neighbor}")
        return "\n".join(context_parts[:max_results])

    def delete_graph(self, chat_id: str) -> bool:
        self._graphs.pop(chat_id, None)
        path = self._graph_path(chat_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def reset_graph(self, chat_id: str) -> nx.DiGraph:
        self.delete_graph(chat_id)
        return self.create_graph(chat_id)

    def get_graph_data(self, chat_id: str) -> GraphData:
        g = self.load_graph(chat_id)
        nodes = [
            GraphNode(id=n, label=data.get("label", n), node_type=data.get("node_type", "entity"), properties=dict(data))
            for n, data in g.nodes(data=True)
        ]
        edges = [
            GraphEdge(source=u, target=v, relation=data.get("relation", "related_to"), weight=data.get("weight", 1.0))
            for u, v, data in g.edges(data=True)
        ]
        return GraphData(nodes=nodes, edges=edges)

    def prune_graph(self, chat_id: str, max_nodes: int = 5000):
        g = self.load_graph(chat_id)
        if g.number_of_nodes() <= max_nodes:
            return
        nodes_sorted = sorted(g.nodes(data=True), key=lambda x: x[1].get("count", 0))
        to_remove = [n for n, _ in nodes_sorted[: g.number_of_nodes() - max_nodes]]
        g.remove_nodes_from(to_remove)
        self._save_graph(chat_id, g)


graph_memory = GraphMemory()
```

- [ ] **Step 2: Create backend/tests/test_graph_memory.py**

```python
import tempfile
import pytest
from graph_memory import GraphMemory


@pytest.fixture
def gm():
    with tempfile.TemporaryDirectory() as tmp:
        yield GraphMemory(graph_dir=tmp)


def test_create_and_load_graph(gm):
    g = gm.create_graph("chat-1")
    assert g.number_of_nodes() == 0
    loaded = gm.load_graph("chat-1")
    assert loaded.number_of_nodes() == 0


def test_add_triple(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    g = gm.load_graph("chat-1")
    assert g.has_edge("user", "pizza")
    assert g["user"]["pizza"]["relation"] == "likes"


def test_query_context(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    gm.add_triple("chat-1", "user", "likes", "coding")
    ctx = gm.query_context("chat-1", ["user"])
    assert "pizza" in ctx
    assert "coding" in ctx


def test_delete_graph(gm):
    gm.create_graph("chat-1")
    assert gm.delete_graph("chat-1") is True
    assert gm.load_graph("chat-1").number_of_nodes() == 0


def test_reset_graph(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    gm.reset_graph("chat-1")
    assert gm.load_graph("chat-1").number_of_nodes() == 0


def test_get_graph_data(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    data = gm.get_graph_data("chat-1")
    assert len(data.nodes) == 2
    assert len(data.edges) == 1


def test_prune_graph(gm):
    gm.create_graph("chat-1")
    for i in range(100):
        gm.add_triple("chat-1", f"entity{i}", "related_to", f"other{i}")
    gm.prune_graph("chat-1", max_nodes=50)
    assert gm.load_graph("chat-1").number_of_nodes() <= 50
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_graph_memory.py -v`
Expected: all tests PASS

---

### Task 3: Ollama LLM Client

**Files:**
- Create: `backend/llm.py`
- Create: `backend/tests/test_llm.py`

**Interfaces:**
- Consumes: `config`
- Produces: `LLMClient` class

- [ ] **Step 1: Create backend/llm.py**

```python
import json
import re
from typing import AsyncGenerator

import httpx

from config import config


class LLMClient:
    def __init__(self, base_url: str = config.ollama_base_url, model: str = config.model_name):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def _ollama_chat(self, messages: list[dict], stream: bool = False):
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if stream:
            return self._stream_response(url, payload)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _stream_response(self, url: str, payload: dict) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done"):
                                return
                        except json.JSONDecodeError:
                            continue

    async def generate(self, system_message: str, messages: list[dict], graph_context: str = "") -> str:
        ollama_messages = []
        if system_message:
            ollama_messages.append({"role": "system", "content": system_message})
        if graph_context:
            ollama_messages.append({
                "role": "system",
                "content": f"Here is relevant context from our conversation history:\n{graph_context}",
            })
        for msg in messages:
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})
        result = await self._ollama_chat(ollama_messages, stream=False)
        return result.get("message", {}).get("content", "")

    async def stream_generate(self, system_message: str, messages: list[dict], graph_context: str = "") -> AsyncGenerator[str, None]:
        ollama_messages = []
        if system_message:
            ollama_messages.append({"role": "system", "content": system_message})
        if graph_context:
            ollama_messages.append({
                "role": "system",
                "content": f"Here is relevant context from our conversation history:\n{graph_context}",
            })
        for msg in messages:
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})
        async for token in await self._stream_response(self.base_url + "/api/chat", {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
        }):
            yield token

    async def extract_entities(self, user_message: str, ai_response: str) -> list[tuple[str, str, str]]:
        prompt = (
            "Extract facts from this conversation as (subject, relation, object) triples.\n"
            "Format each triple on one line like: user | likes | pizza\n"
            "Only output the triples, nothing else.\n\n"
            f"User: {user_message}\n"
            f"Assistant: {ai_response}"
        )
        result = await self._ollama_chat([
            {"role": "system", "content": "You extract knowledge triples from conversations. Output only triples, one per line."},
            {"role": "user", "content": prompt},
        ], stream=False)
        text = result.get("message", {}).get("content", "")
        triples = []
        for line in text.strip().split("\n"):
            line = line.strip()
            parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
            if len(parts) == 3:
                triples.append((parts[0], parts[1], parts[2]))
        return triples


llm_client = LLMClient()
```

- [ ] **Step 2: Create backend/tests/test_llm.py**

```python
import re
import pytest
from llm import LLMClient


@pytest.mark.asyncio
async def test_extract_entities_parses_triples():
    text = "user | likes | pizza\nuser | dislikes | rain"
    triples = []
    for line in text.strip().split("\n"):
        parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
        if len(parts) == 3:
            triples.append((parts[0], parts[1], parts[2]))
    assert len(triples) == 2
    assert triples[0] == ("user", "likes", "pizza")


@pytest.mark.asyncio
async def test_extract_entities_empty():
    text = ""
    triples = []
    for line in text.strip().split("\n"):
        parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
        if len(parts) == 3:
            triples.append((parts[0], parts[1], parts[2]))
    assert len(triples) == 0
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_llm.py -v`
Expected: all tests PASS

---

### Task 4: API Routes + main.py

**Files:**
- Create: `backend/routes/__init__.py`
- Create: `backend/routes/chats.py`
- Create: `backend/routes/messages.py`
- Create: `backend/routes/memory.py`
- Create: `backend/main.py`
- Create: `backend/tests/test_routes.py`

**Interfaces:**
- Consumes: `db`, `graph_memory`, `llm_client`
- Produces: FastAPI app with mounted routers

- [ ] **Step 1: Create backend/routes/__init__.py** (empty file)

- [ ] **Step 2: Create backend/routes/chats.py**

```python
from fastapi import APIRouter, HTTPException

from db import db
from graph_memory import graph_memory
from models import Chat, ChatListResponse, CreateChat, UpdateChat

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats():
    chats = db.list_chats()
    return ChatListResponse(chats=chats)


@router.post("", response_model=Chat, status_code=201)
async def create_chat(body: CreateChat):
    chat = db.create_chat(title=body.title, system_message=body.system_message)
    graph_memory.create_graph(chat.id)
    return chat


@router.get("/{chat_id}", response_model=Chat)
async def get_chat(chat_id: str):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}", response_model=Chat)
async def update_chat(chat_id: str, body: UpdateChat):
    chat = db.update_chat(chat_id, title=body.title, system_message=body.system_message)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.post("/{chat_id}/reset")
async def reset_chat(chat_id: str):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.reset_chat(chat_id)
    graph_memory.reset_graph(chat_id)
    return {"message": "Chat reset successfully"}


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    if not db.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    graph_memory.delete_graph(chat_id)
    return {"message": "Chat deleted"}
```

- [ ] **Step 3: Create backend/routes/messages.py**

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from db import db
from graph_memory import graph_memory
from llm import llm_client
from models import CreateMessage, MessageListResponse

router = APIRouter(prefix="/api/chats/{chat_id}", tags=["messages"])


@router.get("/messages", response_model=MessageListResponse)
async def list_messages(chat_id: str, limit: int = 100, offset: int = 0):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = db.get_messages(chat_id, limit=limit, offset=offset)
    return MessageListResponse(messages=messages)


@router.post("/messages")
async def send_message(chat_id: str, body: CreateMessage):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.add_message(chat_id, "user", body.content)

    graph_memory.load_graph(chat_id)
    recent = db.get_messages(chat_id, limit=20)
    messages_for_llm = [{"role": m.role, "content": m.content} for m in recent]

    graph_ctx = graph_memory.query_context(chat_id, [body.content])

    response = await llm_client.generate(
        system_message=chat.system_message,
        messages=messages_for_llm,
        graph_context=graph_ctx,
    )

    assistant_msg = db.add_message(chat_id, "assistant", response)

    triples = await llm_client.extract_entities(body.content, response)
    for subj, rel, obj in triples:
        graph_memory.add_triple(chat_id, subj, rel, obj)

    return assistant_msg


@router.get("/stream")
async def stream_messages(chat_id: str):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    graph_memory.load_graph(chat_id)
    recent = db.get_messages(chat_id, limit=20)
    messages_for_llm = [{"role": m.role, "content": m.content} for m in recent]
    graph_ctx = graph_memory.query_context(chat_id, [m.content for m in recent[-3:]])

    async def generate():
        full_response = ""
        async for token in llm_client.stream_generate(
            system_message=chat.system_message,
            messages=messages_for_llm,
            graph_context=graph_ctx,
        ):
            full_response += token
            yield f"data: {token}\n\n"

        db.add_message(chat_id, "assistant", full_response)

        if recent:
            user_content = recent[-1].content
            triples = await llm_client.extract_entities(user_content, full_response)
            for subj, rel, obj in triples:
                graph_memory.add_triple(chat_id, subj, rel, obj)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **Step 4: Create backend/routes/memory.py**

```python
from fastapi import APIRouter, HTTPException

from db import db
from graph_memory import graph_memory
from models import GraphData

router = APIRouter(prefix="/api/chats/{chat_id}", tags=["memory"])


@router.get("/graph", response_model=GraphData)
async def get_graph(chat_id: str):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return graph_memory.get_graph_data(chat_id)
```

- [ ] **Step 5: Create backend/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import db
from routes.chats import router as chats_router
from routes.messages import router as messages_router
from routes.memory import router as memory_router

app = FastAPI(title="SLM Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(memory_router)


@app.on_event("startup")
async def startup():
    db.init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Create backend/tests/test_routes.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    async with client as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_chat(client):
    async with client as ac:
        resp = await ac.post("/api/chats", json={"title": "Test", "system_message": "Be friendly"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test"
        assert data["system_message"] == "Be friendly"


@pytest.mark.asyncio
async def test_list_chats(client):
    async with client as ac:
        await ac.post("/api/chats", json={"title": "A"})
        await ac.post("/api/chats", json={"title": "B"})
        resp = await ac.get("/api/chats")
        assert resp.status_code == 200
        assert len(resp.json()["chats"]) >= 2


@pytest.mark.asyncio
async def test_get_chat_not_found(client):
    async with client as ac:
        resp = await ac.get("/api/chats/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_chat(client):
    async with client as ac:
        created = await ac.post("/api/chats", json={"title": "Old"})
        cid = created.json()["id"]
        resp = await ac.patch(f"/api/chats/{cid}", json={"title": "New"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"


@pytest.mark.asyncio
async def test_reset_chat(client):
    async with client as ac:
        created = await ac.post("/api/chats", json={"title": "Test"})
        cid = created.json()["id"]
        resp = await ac.post(f"/api/chats/{cid}/reset")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_chat(client):
    async with client as ac:
        created = await ac.post("/api/chats", json={"title": "Delete"})
        cid = created.json()["id"]
        resp = await ac.delete(f"/api/chats/{cid}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_graph(client):
    async with client as ac:
        created = await ac.post("/api/chats", json={"title": "Graph"})
        cid = created.json()["id"]
        resp = await ac.get(f"/api/chats/{cid}/graph")
        assert resp.status_code == 200
        assert "nodes" in resp.json()
        assert "edges" in resp.json()
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python -m pytest tests/test_routes.py -v`
Expected: all tests PASS (some may require tweaks since test DB state persists)

---

### Task 5: Backend Docker + Frontend Scaffold

**Files:**
- Create: `backend/Dockerfile`
- Create: frontend project via Vite
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useChat.ts`

- [ ] **Step 1: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Scaffold React frontend with Vite**

Run: `cd frontend && npm create vite@latest . -- --template react-ts`

- [ ] **Step 3: Create frontend/src/api/client.ts**

```typescript
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Chat {
  id: string;
  title: string;
  system_message: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface GraphData {
  nodes: { id: string; label: string; node_type: string; properties: Record<string, unknown> }[];
  edges: { source: string; target: string; relation: string; weight: number }[];
}

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  listChats: () => request<{ chats: Chat[] }>("/api/chats"),
  createChat: (title: string, system_message = "") =>
    request<Chat>("/api/chats", { method: "POST", body: JSON.stringify({ title, system_message }) }),
  getChat: (id: string) => request<Chat>(`/api/chats/${id}`),
  updateChat: (id: string, data: Partial<Chat>) =>
    request<Chat>(`/api/chats/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  resetChat: (id: string) =>
    request<{ message: string }>(`/api/chats/${id}/reset`, { method: "POST" }),
  deleteChat: (id: string) =>
    request<{ message: string }>(`/api/chats/${id}`, { method: "DELETE" }),
  listMessages: (chatId: string) =>
    request<{ messages: Message[] }>(`/api/chats/${chatId}/messages`),
  sendMessage: (chatId: string, content: string) =>
    request<Message>(`/api/chats/${chatId}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  streamUrl: (chatId: string) => `${API_BASE}/api/chats/${chatId}/stream`,
  getGraph: (chatId: string) => request<GraphData>(`/api/chats/${chatId}/graph`),
};
```

- [ ] **Step 4: Create frontend/src/hooks/useChat.ts**

```typescript
import { useState, useEffect, useCallback, useRef } from "react";
import { api, Chat, Message } from "../api/client";

export function useChat() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [loading, setLoading] = useState(false);
  const activeChat = chats.find((c) => c.id === activeChatId) || null;

  const loadChats = useCallback(async () => {
    const data = await api.listChats();
    setChats(data.chats);
  }, []);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  const selectChat = useCallback(async (id: string) => {
    setActiveChatId(id);
    setStreamingContent("");
    const data = await api.listMessages(id);
    setMessages(data.messages);
  }, []);

  const createChat = useCallback(async (title?: string) => {
    const chat = await api.createChat(title || "New Chat");
    setChats((prev) => [chat, ...prev]);
    return chat;
  }, []);

  const updateChat = useCallback(async (id: string, data: Partial<Chat>) => {
    const updated = await api.updateChat(id, data);
    setChats((prev) => prev.map((c) => (c.id === id ? updated : c)));
  }, []);

  const deleteChat = useCallback(async (id: string) => {
    await api.deleteChat(id);
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
      setMessages([]);
    }
  }, [activeChatId]);

  const resetChat = useCallback(async (id: string) => {
    await api.resetChat(id);
    setMessages([]);
    setStreamingContent("");
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!activeChatId) return;
    setLoading(true);
    setStreamingContent("");

    const userMsg: Message = {
      id: "temp",
      chat_id: activeChatId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const streamUrl = api.streamUrl(activeChatId);
    const res = await fetch(streamUrl, {
      method: "GET",
      headers: { Accept: "text/event-stream" },
    });

    if (!res.ok) {
      setLoading(false);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      setLoading(false);
      return;
    }

    const decoder = new TextDecoder();
    let full = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            setMessages((prev) => [
              ...prev,
              {
                id: "streamed",
                chat_id: activeChatId,
                role: "assistant",
                content: full,
                created_at: new Date().toISOString(),
              },
            ]);
            setStreamingContent("");
          } else {
            full += data;
            setStreamingContent(full);
          }
        }
      }
    }
    setLoading(false);
  }, [activeChatId]);

  return {
    chats,
    activeChatId,
    activeChat,
    messages,
    streamingContent,
    loading,
    selectChat,
    createChat,
    updateChat,
    deleteChat,
    resetChat,
    sendMessage,
  };
}
```

---

### Task 6: React Frontend Components

**Files:**
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/ChatList.tsx`
- Create: `frontend/src/components/ChatWindow.tsx`
- Create: `frontend/src/components/MessageBubble.tsx`
- Create: `frontend/src/components/MessageInput.tsx`
- Create: `frontend/src/components/SystemMessageEditor.tsx`

- [ ] **Step 1: Create frontend/src/components/ChatList.tsx**

```tsx
import { Chat } from "../api/client";

interface Props {
  chats: Chat[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

export function ChatList({ chats, activeChatId, onSelect, onCreate, onDelete }: Props) {
  return (
    <div style={{ width: 260, borderRight: "1px solid #333", height: "100vh", display: "flex", flexDirection: "column", background: "#1a1a1a" }}>
      <div style={{ padding: "12px", borderBottom: "1px solid #333" }}>
        <button
          onClick={onCreate}
          style={{ width: "100%", padding: "8px", background: "#2d2d2d", color: "#fff", border: "1px solid #555", borderRadius: 6, cursor: "pointer" }}
        >
          + New Chat
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => onSelect(chat.id)}
            style={{
              padding: "10px 12px",
              cursor: "pointer",
              background: chat.id === activeChatId ? "#2d2d2d" : "transparent",
              borderBottom: "1px solid #2a2a2a",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ color: "#ddd", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
              {chat.title}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(chat.id); }}
              style={{ background: "none", border: "none", color: "#666", cursor: "pointer", fontSize: 12 }}
            >
              x
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/src/components/MessageBubble.tsx**

```tsx
import { Message } from "../api/client";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 12 }}>
      <div
        style={{
          maxWidth: "70%",
          padding: "10px 14px",
          borderRadius: 12,
          background: isUser ? "#2b5278" : "#2d2d2d",
          color: "#eee",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {message.content}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create frontend/src/components/MessageInput.tsx**

```tsx
import { useState, FormEvent } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} style={{ padding: "12px", borderTop: "1px solid #333", display: "flex", gap: 8 }}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: "10px",
          borderRadius: 8,
          border: "1px solid #555",
          background: "#2d2d2d",
          color: "#eee",
          outline: "none",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        style={{
          padding: "10px 20px",
          borderRadius: 8,
          border: "none",
          background: disabled ? "#444" : "#2b5278",
          color: "#fff",
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        Send
      </button>
    </form>
  );
}
```

- [ ] **Step 4: Create frontend/src/components/SystemMessageEditor.tsx**

```tsx
import { useState } from "react";

interface Props {
  systemMessage: string;
  onSave: (msg: string) => void;
}

export function SystemMessageEditor({ systemMessage, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(systemMessage);

  const handleSave = () => {
    onSave(value);
    setOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        style={{ background: "none", border: "1px solid #555", color: "#aaa", borderRadius: 4, padding: "4px 8px", cursor: "pointer", fontSize: 12 }}
      >
        System Prompt
      </button>
      {open && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
        }}>
          <div style={{ background: "#1a1a1a", padding: 20, borderRadius: 12, width: 500, maxWidth: "90vw" }}>
            <h3 style={{ color: "#eee", margin: "0 0 12px" }}>System Message</h3>
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              rows={6}
              style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #555", background: "#2d2d2d", color: "#eee", resize: "vertical" }}
            />
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
              <button onClick={() => setOpen(false)} style={{ padding: "6px 12px", background: "#333", color: "#eee", border: "none", borderRadius: 6, cursor: "pointer" }}>Cancel</button>
              <button onClick={handleSave} style={{ padding: "6px 12px", background: "#2b5278", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}>Save</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 5: Create frontend/src/components/ChatWindow.tsx**

```tsx
import { Chat, Message } from "../api/client";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { SystemMessageEditor } from "./SystemMessageEditor";

interface Props {
  chat: Chat;
  messages: Message[];
  streamingContent: string;
  loading: boolean;
  onSend: (content: string) => void;
  onUpdateChat: (id: string, data: Partial<Chat>) => void;
  onReset: (id: string) => void;
}

export function ChatWindow({ chat, messages, streamingContent, loading, onSend, onUpdateChat, onReset }: Props) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #333", display: "flex", justifyContent: "space-between", alignItems: "center", background: "#1a1a1a" }}>
        <h2 style={{ margin: 0, color: "#eee", fontSize: 16 }}>{chat.title}</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <SystemMessageEditor
            systemMessage={chat.system_message}
            onSave={(msg) => onUpdateChat(chat.id, { system_message: msg })}
          />
          <button
            onClick={() => onReset(chat.id)}
            style={{ background: "none", border: "1px solid #555", color: "#aaa", borderRadius: 4, padding: "4px 8px", cursor: "pointer", fontSize: 12 }}
          >
            Reset
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 16, background: "#121212" }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {streamingContent && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
            <div style={{ maxWidth: "70%", padding: "10px 14px", borderRadius: 12, background: "#2d2d2d", color: "#eee", whiteSpace: "pre-wrap" }}>
              {streamingContent}
            </div>
          </div>
        )}
      </div>
      <MessageInput onSend={onSend} disabled={loading} />
    </div>
  );
}
```

- [ ] **Step 6: Create frontend/src/App.tsx**

```tsx
import { ChatList } from "./components/ChatList";
import { ChatWindow } from "./components/ChatWindow";
import { useChat } from "./hooks/useChat";

export default function App() {
  const {
    chats, activeChatId, activeChat, messages, streamingContent, loading,
    selectChat, createChat, updateChat, deleteChat, resetChat, sendMessage,
  } = useChat();

  return (
    <div style={{ display: "flex", height: "100vh", background: "#121212", color: "#eee", fontFamily: "system-ui, sans-serif" }}>
      <ChatList
        chats={chats}
        activeChatId={activeChatId}
        onSelect={selectChat}
        onCreate={() => createChat()}
        onDelete={deleteChat}
      />
      {activeChat ? (
        <ChatWindow
          chat={activeChat}
          messages={messages}
          streamingContent={streamingContent}
          loading={loading}
          onSend={sendMessage}
          onUpdateChat={updateChat}
          onReset={resetChat}
        />
      ) : (
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#666" }}>
          Select or create a chat to begin
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 7: Update frontend/src/main.tsx to use App**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

---

### Task 7: Docker Compose + Frontend Docker + README

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`
- Create: `README.md`

- [ ] **Step 1: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

- [ ] **Step 2: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - slm_data:/app/data
    environment:
      - SLM_OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  ollama_data:
  slm_data:
```

- [ ] **Step 4: Create README.md**

```markdown
# SLM Chat

A personal AI friend chat application powered by `floxy/LFM2.5-Instruct:1.2b` via ollama, featuring per-chat graph-based memory.

## Quick Start

```bash
docker compose up -d
```

Open http://localhost in your browser.

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Pull the model

```bash
ollama pull floxy/LFM2.5-Instruct:1.2b
```

## Features

- Multiple chats with per-chat system messages
- Graph-based long-term memory (NetworkX)
- SSE streaming responses
- NSFW-friendly (no content filtering)
- Docker compose deployment
```
