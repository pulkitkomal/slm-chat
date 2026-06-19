# SLM Chat — Personal AI Friend

## Overview

A chat application powered by `floxy/LFM2.5-Instruct:1.2b` via ollama, designed as a personal friend with long-term per-chat graph memory, NSFW-allowed, with a React frontend and FastAPI backend.

## Architecture

```
┌─────────┐  HTTP/SSE   ┌──────────┐  ollama API  ┌────────┐
│ React   │ ◄─────────► │ FastAPI  │ ◄───────────► │ ollama │
│ Frontend│             │ Backend  │               │ server │
└─────────┘             └────┬─────┘               └────────┘
                             │
                    ┌────────┴────────┐
                    │  SQLite (chats, │
                    │  messages)      │
                    ├─────────────────┤
                    │  NetworkX graph │
                    │  (per chat .json│
                    │   files)        │
                    └─────────────────┘
```

## Project Structure

```
slm-chat/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (model, port, DB path, etc.)
│   ├── db.py                # SQLite setup + CRUD for chats/messages
│   ├── models.py            # Pydantic request/response models
│   ├── graph_memory.py      # NetworkX graph per chat
│   ├── llm.py               # Ollama client wrapper
│   ├── routes/
│   │   ├── chats.py         # Chat CRUD + reset
│   │   ├── messages.py      # Message send/stream/list
│   │   └── memory.py        # Graph introspection
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatList.tsx
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── SystemMessageEditor.tsx
│   │   ├── hooks/useChat.ts
│   │   └── api/client.ts
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml        # orchestrates backend + frontend + ollama
└── README.md
```

## Data Flow

1. User types a message → React sends `POST /api/chats/{id}/messages`
2. Backend queries the chat's NetworkX graph for relevant context
3. Backend builds prompt: system message + graph context + recent messages
4. Backend streams response from ollama via SSE (`GET /api/chats/{id}/stream`)
5. Response saved to SQLite
6. Both user message and AI response are entity-extracted into the graph (async)

## Graph Memory Design

Per-chat NetworkX graph stored as JSON files.

**Node types:**
- `User` — name, preferences, biographical facts
- `Topic` — subjects discussed, with importance weight
- `Preference` — likes/dislikes (NSFW included)
- `Event` — past interactions, shared experiences

**Edge types:**
- `likes`, `dislikes`, `discusses`, `mentions`, `related_to`

**Graph query before each response:**
- Extract entities from current message via the same ollama model with a concise extraction prompt
- Traverse k-hop neighbors for relevant context
- Return top-N triples as natural-language context snippet

**Memory pruning:**
- Recency timestamp + access count per edge
- Stale edges deprioritized; no hard deletion
- Configurable node limit per chat (default: 5000)

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/chats` | List all chats |
| `POST` | `/api/chats` | Create chat (with system message) |
| `GET` | `/api/chats/{id}` | Get chat details |
| `PATCH` | `/api/chats/{id}` | Update system message |
| `POST` | `/api/chats/{id}/reset` | Wipe messages + rebuild graph |
| `DELETE` | `/api/chats/{id}` | Delete chat |
| `GET` | `/api/chats/{id}/messages` | List messages (paginated) |
| `POST` | `/api/chats/{id}/messages` | Send message, get response |
| `GET` | `/api/chats/{id}/stream` | SSE stream for real-time response |
| `GET` | `/api/chats/{id}/graph` | Inspect graph |

## Frontend Components

```
App
├── ChatList              ← sidebar
│   └── ChatListItem
├── ChatWindow            ← main content
│   ├── Header
│   │   ├── ChatTitle
│   │   ├── SystemMessageEditor
│   │   └── ResetButton
│   ├── MessageList
│   │   └── MessageBubble
│   └── MessageInput
└── NewChatButton
```

## Docker

Three services in `docker-compose.yml`:
- **ollama** — official ollama image, model pulled at startup
- **backend** — FastAPI app, connects to ollama
- **frontend** — React build served via nginx

Named volume for SQLite DB + graph files.

## Error Handling

- **Ollama down:** `503` response, frontend shows "Model unavailable"
- **Stream interruption:** Frontend reconnects SSE; backend handles partial message cleanup
- **Graph corruption:** On load failure, rebuilds empty graph
- **NSFW guardrails:** None by design
- **Prompt overflow:** Trims oldest messages before context window overflow; keeps graph context prioritized
