import json
import re
from typing import AsyncGenerator

import httpx

from config import config


_MAX_ENTITY_LENGTH = 40


def _is_valid_entity(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    if len(name) > _MAX_ENTITY_LENGTH:
        return False
    words = name.split()
    if len(words) > 5:
        return False
    if name.lower() in ("user", "assistant", "system"):
        return True
    if len(words) >= 3 and re.search(r"\b(is|are|was|were|have|has|had|been)\b", name):
        return False
    if name.lower() in ("object", "subject", "relation", "person", "thing"):
        return False
    return True


def _normalize(name: str) -> str:
    return name.strip().lower()


class LLMClient:
    def __init__(self, base_url: str = config.ollama_base_url, model: str = config.model_name):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def _ollama_chat(self, messages: list[dict], stream: bool = False):
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if stream:
            return self._stream_response(url, payload)
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def _stream_response(self, url: str, payload: dict) -> AsyncGenerator[str, None]:
        async with self._client.stream("POST", url, json=payload) as resp:
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
                "content": f"You remember these facts about the user from past conversation. Use them to answer accurately:\n{graph_context}",
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
                "content": f"You remember these facts about the user from past conversation. Use them to answer accurately:\n{graph_context}",
            })
        for msg in messages:
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})
        async for token in self._stream_response(self.base_url + "/api/chat", {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
        }):
            yield token

    def _parse_triples(self, text: str) -> list[tuple[str, str, str]]:
        """Parse triples from LLM output. Handles pipe-separated and space-separated formats."""
        raw = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
            if len(parts) == 3:
                raw.append(tuple(parts))
                continue
            parts = line.split()
            if len(parts) == 3:
                raw.append(tuple(parts))
        return raw

    async def extract_entities(self, user_message: str, ai_response: str) -> list[tuple[str, str, str]]:
        prompt = (
            "Extract facts from this conversation as triples.\n"
            "Each line: subject | relation | object\n"
            "Only use exact words from the conversation.\n"
            "Example:\n"
            "user | likes | fantasy books\n"
            f"User: {user_message}\n"
            f"Assistant: {ai_response}"
        )
        result = await self._ollama_chat([
            {"role": "system", "content": "Extract triples from the conversation. Format: subject | relation | object"},
            {"role": "user", "content": prompt},
        ], stream=False)
        text = result.get("message", {}).get("content", "")
        raw = self._parse_triples(text)

        seen = set()
        clean = []
        for subj, rel, obj in raw:
            subj_n = _normalize(subj)
            obj_n = _normalize(obj)
            rel_l = rel.strip().lower()
            if not _is_valid_entity(subj_n) or not _is_valid_entity(obj_n):
                continue
            if subj_n == obj_n:
                continue
            key = (subj_n, rel_l, obj_n)
            if key in seen:
                continue
            seen.add(key)
            clean.append((subj_n, rel_l, obj_n))
        return clean


    async def classify_emotion(self, user_message: str) -> tuple[str, float]:
        prompt = (
            "Classify the emotional state from this message.\n"
            "Emotions: calm, happy, sad, angry, anxious\n"
            "Reply: emotion | intensity (0.0-1.0)\n"
            f"Message: {user_message}"
        )
        result = await self._ollama_chat([
            {"role": "system", "content": "Classify the emotion. Reply with: emotion | intensity"},
            {"role": "user", "content": prompt},
        ], stream=False)
        text = result.get("message", {}).get("content", "").strip()
        parts = [p.strip() for p in text.split("|")]
        emotion = parts[0].lower() if parts else "calm"
        VALID = {"calm", "happy", "sad", "angry", "anxious"}
        if emotion not in VALID:
            emotion = "calm"
        intensity = 0.5
        if len(parts) > 1:
            try:
                intensity = max(0.0, min(1.0, float(parts[1])))
            except ValueError:
                pass
        return emotion, intensity


llm_client = LLMClient()
