# File: backend/services/notifications_service.py
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class NotificationsError(Exception):
    pass

class NotificationsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,         -- 'mail', 'system', 'order', etc.
                title TEXT NOT NULL,
                body TEXT,
                link TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                read_at TEXT,
                deleted_at TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications(user_id)")
            conn.commit()

    def create_notification(self, user_id: int, type: str, title: str, body: str = "", link: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO notifications (user_id, type, title, body, link)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, type, title, body, link))
            conn.commit()
            return cur.lastrowid

    def list_unread(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM notifications
                WHERE user_id = ? AND read_at IS NULL AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def list_recent(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM notifications
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(r) for r in cur.fetchall()]

    def mark_read(self, notification_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications
                SET read_at = datetime('now')
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (notification_id, user_id))
            conn.commit()

    def mark_all_read(self, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications
                SET read_at = datetime('now')
                WHERE user_id = ? AND deleted_at IS NULL AND read_at IS NULL
            """, (user_id,))
            conn.commit()

    def delete(self, notification_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications
                SET deleted_at = datetime('now')
                WHERE id = ? AND user_id = ?
            """, (notification_id, user_id))
            conn.commit()
