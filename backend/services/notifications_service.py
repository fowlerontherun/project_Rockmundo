# File: backend/services/notifications_service.py
import sqlite3
from typing import Optional, Dict, Any, List
from utils.db import get_conn

class NotificationsError(Exception):
    pass

class NotificationsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # --- CRUD / helpers ---
    def create(self, user_id: int, title: str, body: str = "", type_: str = "system") -> int:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO notifications (user_id, type, title, body)
                       VALUES (?, ?, ?, ?)""",
                (user_id, type_, title, body),
            )
            return int(cur.lastrowid)

    def list(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, user_id, type, title, body, created_at, read_at
                       FROM notifications
                       WHERE user_id = ?
                       ORDER BY COALESCE(read_at, '9999-12-31') IS NOT NULL, created_at DESC
                       LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            )
            return [dict(r) for r in cur.fetchall()]

    def unread_count(self, user_id: int) -> int:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read_at IS NULL", (user_id,))
            return int(cur.fetchone()[0])

    def mark_read(self, notif_id: int, user_id: int) -> bool:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE notifications
                       SET read_at = datetime('now')
                       WHERE id = ? AND user_id = ? AND read_at IS NULL""",
                (notif_id, user_id),
            )
            return cur.rowcount > 0

    def mark_all_read(self, user_id: int) -> int:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE notifications
                       SET read_at = datetime('now')
                       WHERE user_id = ? AND read_at IS NULL""",
                (user_id,),
            )
            return cur.rowcount
