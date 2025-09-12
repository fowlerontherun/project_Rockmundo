import sys
import sqlite3
from pathlib import Path

import pytest

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from services import chat_service  # noqa: E402


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db = tmp_path / "chat.db"
    monkeypatch.setattr(chat_service, "DB_PATH", str(db))
    sqlite3.connect(chat_service.DB_PATH).close()


def test_direct_messages_persist():
    msg = {"sender_id": 1, "recipient_id": 2, "content": "hi"}
    chat_service.send_message(msg)

    history1 = chat_service.get_user_chat_history(1)
    history2 = chat_service.get_user_chat_history(2)

    assert history1["direct_messages"] == history2["direct_messages"]
    assert history1["direct_messages"][0]["content"] == "hi"


def test_group_messages_persist():
    chat_service.send_group_chat({"group_id": "band", "sender_id": 1, "content": "hello"})
    chat_service.add_user_to_group("band", 2)

    history = chat_service.get_user_chat_history(2)

    assert "band" in history["group_chats"]
    assert history["group_chats"]["band"][0]["content"] == "hello"

