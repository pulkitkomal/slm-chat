import asyncio

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
    recent = db.get_messages(chat_id, limit=10)
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
async def stream_messages(chat_id: str, q: str = ""):
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if q:
        db.add_message(chat_id, "user", q)

    graph_memory.load_graph(chat_id)
    recent = db.get_messages(chat_id, limit=10)
    messages_for_llm = [{"role": m.role, "content": m.content} for m in recent]
    graph_ctx = graph_memory.query_context(chat_id, [q] + [m.content for m in recent[-3:]])

    async def extract_and_update(user_msg: str, ai_response: str):
        try:
            triples = await llm_client.extract_entities(user_msg, ai_response)
            for subj, rel, obj in triples:
                graph_memory.add_triple(chat_id, subj, rel, obj)
        except Exception:
            pass

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

        asyncio.create_task(extract_and_update(q, full_response))

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
