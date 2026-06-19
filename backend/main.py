from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import db
from routes.agents import router as agents_router
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

app.include_router(agents_router)
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(memory_router)


@app.on_event("startup")
async def startup():
    db.init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
