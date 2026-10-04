import sqlite3

from services.notifications_service import NotificationsService


def _db(path):
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT
        )""")


def test_notifications_keep_account_notices_but_filter_gameplay(tmp_path):
    path = str(tmp_path / "notifications.db")
    _db(path)
    svc = NotificationsService(path)
    svc.create(7, "Security", type_="system")
    svc.create(7, "Character A", type_="event", character_id=101)
    svc.create(7, "Character B", type_="event", character_id=202)

    titles = [n["title"] for n in svc.list(7, character_id=101)]
    assert "Security" in titles
    assert "Character A" in titles
    assert "Character B" not in titles
