# File: backend/services/notifications_service.py

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import resolves differently when executed as package vs. tests.
try:  # pragma: no cover - primary import when project is installed
    from services.discord_service import DiscordServiceError, send_message
except Exception:  # pragma: no cover - fallback or noop if unavailable
    try:  # running in tests without package context
        from .discord_service import DiscordServiceError, send_message
    except Exception:  # ultimate fallback, define no-op implementation
        class DiscordServiceError(Exception):
            pass

        def send_message(*args, **kwargs):  # type: ignore
            return None
from utils.db import get_conn
from backend.realtime.social_gateway import publish_notification


class NotificationsError(Exception):
    pass

class NotificationsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # --- CRUD / helpers ---
    def create(
        self,
        user_id: int,
        title: str,
        body: str = "",
        type_: str = "system",
        send_to_discord: bool = False,
    ) -> int:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO notifications (user_id, type, title, body)
                       VALUES (?, ?, ?, ?)""",
                (user_id, type_, title, body),
            )
            notif_id = int(cur.lastrowid)

        if send_to_discord:
            try:
                content = f"{title}\n{body}".strip()
                send_message(content)
            except DiscordServiceError as exc:
                print(f"Discord notification failed: {exc}")

        # Fire-and-forget realtime event
        try:
            asyncio.create_task(
                publish_notification(user_id, notif_id, title, body, type_)
            )
        except RuntimeError:
            # No running loop (e.g., sync context); create one ad-hoc
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                publish_notification(user_id, notif_id, title, body, type_)
            )
            loop.close()

        return notif_id

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

    # --- Convenience ---
    def record_event(self, user_id: int, message: str, timestamp: Optional[str] = None) -> int:
        """Record a simple event notification for a user.

        Parameters
        ----------
        user_id: int
            The user receiving the notification.
        message: str
            Description of the event.
        timestamp: Optional[str]
            Optional ISO timestamp stored in the body. If omitted the current
            UTC time is used.
        """

        ts = timestamp or datetime.utcnow().isoformat()
        return self.create(user_id, message, body=ts, type_="event")
