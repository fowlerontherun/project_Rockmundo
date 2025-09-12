"""Admin notification service managing persistent alerts.

This module provides CRUD helpers for a simple ``admin_notifications`` table
stored in SQLite.  Each notification includes a severity level and a boolean
read state so the admin interface can highlight unread messages.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.utils.db import get_conn


class AdminNotificationsService:
    """Service layer for admin notifications."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        with get_conn(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    read INTEGER NOT NULL DEFAULT 0
                );
                """
            )

    # ------------------------------------------------------------------
    def create(self, message: str, severity: str = "info") -> int:
        """Insert a new admin notification and return its id."""
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO admin_notifications (message, severity) VALUES (?, ?)",
                (message, severity),
            )
            return int(cur.lastrowid)

    def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Return notifications ordered by unread first then newest."""
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, message, severity, created_at, read
                FROM admin_notifications
                ORDER BY read ASC, created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            return [dict(r) for r in cur.fetchall()]

    def mark_read(self, notif_id: int) -> bool:
        """Mark a notification as read."""
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE admin_notifications SET read = 1 WHERE id = ? AND read = 0",
                (notif_id,),
            )
            return cur.rowcount > 0

    def delete(self, notif_id: int) -> bool:
        """Remove a notification."""
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM admin_notifications WHERE id = ?", (notif_id,))
            return cur.rowcount > 0

    def unread_count(self) -> int:
        """Return the number of unread notifications."""
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM admin_notifications WHERE read = 0"
            )
            return int(cur.fetchone()[0])
