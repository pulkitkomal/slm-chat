import pytest
from httpx import AsyncClient, ASGITransport

from db import db

db.db_path = ":memory:"
db._mem_conn = None
db.init_db()

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
