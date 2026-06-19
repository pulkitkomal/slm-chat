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
