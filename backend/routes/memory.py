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
