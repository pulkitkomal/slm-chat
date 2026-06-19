# SLM Chat

A personal AI friend chat application powered by `floxy/LFM2.5-Instruct:1.2b` via ollama, featuring per-chat graph-based memory.

## Quick Start

```bash
docker compose up -d
```

Open http://localhost:8081 in your browser.

Backend API at http://localhost:8002. Ollama at http://localhost:11434.

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
