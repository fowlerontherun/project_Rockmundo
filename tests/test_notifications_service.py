import sqlite3
from backend.services.notifications_service import NotificationsService


def _setup_db(path):
    with sqlite3.connect(path) as conn:
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
        conn.execute(
            """
            INSERT INTO notifications (user_id, type, title, body, created_at, read_at)
            VALUES (1, 'system', 'read', '', '2023-01-01', '2023-01-05')
            """
        )
        conn.execute(
            """
            INSERT INTO notifications (user_id, type, title, body, created_at)
            VALUES (1, 'system', 'unread1', '', '2023-01-02')
            """
        )
        conn.execute(
            """
            INSERT INTO notifications (user_id, type, title, body, created_at)
            VALUES (1, 'system', 'unread2', '', '2023-01-03')
            """
        )
        conn.commit()


def test_unread_first(tmp_path):
    db_path = tmp_path / 'db.sqlite'
    _setup_db(db_path)
    svc = NotificationsService(str(db_path))
    items = svc.list(1)
    titles = [i['title'] for i in items]
    assert titles == ['unread2', 'unread1', 'read']
    assert items[0]['read_at'] is None
    assert items[-1]['read_at'] is not None
