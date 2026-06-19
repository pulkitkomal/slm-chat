import pytest
from db import Database


@pytest.fixture
def db():
    d = Database(":memory:")
    d.init_db()
    return d


def test_create_chat(db):
    chat = db.create_chat("Test Chat", "You are a friend.")
    assert chat.title == "Test Chat"
    assert chat.system_message == "You are a friend."
    assert chat.id is not None


def test_get_chat(db):
    created = db.create_chat("Test", "msg")
    found = db.get_chat(created.id)
    assert found is not None
    assert found.id == created.id


def test_get_chat_not_found(db):
    assert db.get_chat("nonexistent") is None


def test_list_chats(db):
    db.create_chat("A")
    db.create_chat("B")
    chats = db.list_chats()
    assert len(chats) == 2


def test_update_chat(db):
    chat = db.create_chat("Old")
    updated = db.update_chat(chat.id, title="New")
    assert updated.title == "New"


def test_delete_chat(db):
    chat = db.create_chat("Delete me")
    assert db.delete_chat(chat.id) is True
    assert db.get_chat(chat.id) is None


def test_add_message(db):
    chat = db.create_chat("Chat")
    msg = db.add_message(chat.id, "user", "Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.chat_id == chat.id


def test_get_messages(db):
    chat = db.create_chat("Chat")
    db.add_message(chat.id, "user", "Hi")
    db.add_message(chat.id, "assistant", "Hello!")
    msgs = db.get_messages(chat.id)
    assert len(msgs) == 2


def test_reset_chat(db):
    chat = db.create_chat("Chat")
    db.add_message(chat.id, "user", "Hi")
    db.reset_chat(chat.id)
    assert len(db.get_messages(chat.id)) == 0
