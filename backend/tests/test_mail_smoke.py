# File: backend/tests/test_mail_smoke.py
import pytest
from utils.db import aget_conn
from backend.services.mail_service import MailService
from backend.services.notifications_service import NotificationsService

MAIL_DDL = """
CREATE TABLE IF NOT EXISTS mail_threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT NOT NULL,
  created_by INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS mail_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  sender_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS mail_participants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  last_read_message_id INTEGER DEFAULT 0,
  UNIQUE (thread_id, user_id)
);
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  read_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_nm ON notifications(user_id, created_at);
"""

async def setup_db(path: str) -> None:
    async with aget_conn(path) as conn:
        await conn.executescript(MAIL_DDL)


@pytest.mark.asyncio
async def test_compose_and_unread_badge(tmp_path):
    db = str(tmp_path / "test_mail.db")
    await setup_db(db)
    notif = NotificationsService(db_path=db)
    mail = MailService(db_path=db, notifications=notif)

    # compose to user 2
    res = mail.compose(sender_id=1, recipient_ids=[2], subject="Hello", body="Hi there!")
    assert res["thread_id"] > 0 and res["message_id"] > 0

    # unread badge for user 2 shows 1 mail and 1 notification (mail fan-out)
    badge = mail.unread_badge(user_id=2)
    assert badge["mail"] >= 1
    assert badge["notifications"] >= 1
