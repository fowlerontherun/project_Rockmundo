import logging
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.services import notifications_service as ns


@pytest.fixture
def temp_db(tmp_path):
    db = tmp_path / "notif.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            read_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return str(db)


def test_discord_warning_logged(monkeypatch, caplog, temp_db):
    service = ns.NotificationsService(db_path=temp_db)

    def mock_send_message(content):
        raise ns.DiscordServiceError("boom")

    monkeypatch.setattr(ns, "send_message", mock_send_message)
    monkeypatch.setattr(ns, "publish_notification", lambda *a, **k: None)
    monkeypatch.setattr(ns.asyncio, "create_task", lambda *a, **k: None)

    with caplog.at_level(logging.WARNING):
        service.create(1, "title", "body", send_to_discord=True)

    assert "Discord notification failed: boom" in caplog.text
