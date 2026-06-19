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
