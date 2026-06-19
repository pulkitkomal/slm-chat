from fastapi import APIRouter, HTTPException

from agents import get_agent
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
    title = body.title
    system_message = body.system_message
    agent_id = body.agent_id
    if agent_id:
        agent = get_agent(agent_id)
        if agent:
            title = agent.name
            system_message = agent.system_message
    chat = db.create_chat(title=title, system_message=system_message, agent_id=agent_id)
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
