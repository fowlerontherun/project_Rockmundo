# File: backend/services/mail_service.py
from typing import List, Dict, Any, Optional
import sqlite3

from utils.db import get_conn
from services.notifications_service import NotificationsService
from core.errors import AppError, MailNoRecipientsError

class MailService:
    def __init__(self, db_path: Optional[str] = None, notifications: Optional[NotificationsService] = None):
        self.db_path = db_path
        self.notifications = notifications or NotificationsService(db_path=self.db_path)

    # ---- helpers ----
    def _add_participants(self, cur: sqlite3.Cursor, thread_id: int, user_ids: List[int]) -> None:
        for uid in user_ids:
            cur.execute(
                """INSERT OR IGNORE INTO mail_participants (thread_id, user_id)
                       VALUES (?, ?)""",
                (thread_id, uid),
            )

    def _notify(self, recipient_ids: List[int], title: str, body: str) -> None:
        for uid in recipient_ids:
            self.notifications.create(user_id=uid, type_="mail", title=title, body=body)

    # ---- public API ----
    def compose(self, sender_id: int, recipient_ids: List[int], subject: str, body: str) -> Dict[str, Any]:
        if not recipient_ids:
            raise MailNoRecipientsError("At least one recipient is required.")
        if not subject or not subject.strip():
            raise AppError("Subject is required.", code="MAIL_SUBJECT_REQUIRED")
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO mail_threads (subject, created_by) VALUES (?, ?)", (subject.strip(), sender_id))
            thread_id = int(cur.lastrowid)

            self._add_participants(cur, thread_id, [sender_id] + recipient_ids)
            cur.execute(
                """INSERT INTO mail_messages (thread_id, sender_id, body)
                       VALUES (?, ?, ?)""",
                (thread_id, sender_id, body),
            )
            message_id = int(cur.lastrowid)

            # mark sender read-through latest
            cur.execute(
                """UPDATE mail_participants SET last_read_message_id = ?
                       WHERE thread_id=? AND user_id=?""",
                (message_id, thread_id, sender_id),
            )

            # notifications
            self._notify(recipient_ids, title=f"New message: {subject.strip()}", body=body[:140])

            return {"thread_id": thread_id, "message_id": message_id}

    def reply(self, thread_id: int, sender_id: int, body: str) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, subject FROM mail_threads WHERE id=?", (thread_id,))
            row = cur.fetchone()
            if not row:
                raise AppError("Thread not found.", code="MAIL_THREAD_NOT_FOUND")
            subject = row[1]

            # ensure sender is participant
            cur.execute(
                "INSERT OR IGNORE INTO mail_participants (thread_id, user_id) VALUES (?, ?)",
                (thread_id, sender_id),
            )

            cur.execute(
                """INSERT INTO mail_messages (thread_id, sender_id, body)
                       VALUES (?, ?, ?)""", (thread_id, sender_id, body)
            )
            message_id = int(cur.lastrowid)

            # update sender last_read
            cur.execute(
                """UPDATE mail_participants SET last_read_message_id = ?
                       WHERE thread_id=? AND user_id=?""",
                (message_id, thread_id, sender_id),
            )

            # notify all other participants
            cur.execute("SELECT user_id FROM mail_participants WHERE thread_id=? AND user_id != ?", (thread_id, sender_id))
            recipients = [int(r[0]) for r in cur.fetchall()]
            if recipients:
                self._notify(recipients, title=f"New reply: {subject}", body=body[:140])

            return {"thread_id": thread_id, "message_id": message_id}

    def list_threads(self, user_id: int, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """WITH last_msg AS (
                       SELECT thread_id, MAX(id) AS last_id, MAX(created_at) AS last_at
                       FROM mail_messages GROUP BY thread_id
                     ), unread AS (
                       SELECT p.thread_id,
                              SUM(CASE WHEN m.id > p.last_read_message_id AND m.sender_id != p.user_id
                                       THEN 1 ELSE 0 END) AS unread_count
                       FROM mail_participants p
                       JOIN mail_messages m ON m.thread_id = p.thread_id
                       WHERE p.user_id = ?
                       GROUP BY p.thread_id
                     )
                     SELECT t.id AS thread_id, t.subject, t.created_by, t.created_at,
                            COALESCE(u.unread_count, 0) AS unread,
                            l.last_id, l.last_at
                     FROM mail_threads t
                     JOIN mail_participants p ON p.thread_id = t.id AND p.user_id = ?
                     LEFT JOIN last_msg l ON l.thread_id = t.id
                     LEFT JOIN unread u ON u.thread_id = t.id
                     ORDER BY l.last_at DESC NULLS LAST, t.created_at DESC
                     LIMIT ? OFFSET ?""",
                (user_id, user_id, limit, offset),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def get_thread(self, thread_id: int, user_id: int, mark_read: bool = True) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            # thread
            cur.execute("SELECT id, subject, created_by, created_at FROM mail_threads WHERE id=?", (thread_id,))
            t = cur.fetchone()
            if not t:
                raise AppError("Thread not found.", code="MAIL_THREAD_NOT_FOUND")

            # ensure participant
            cur.execute("INSERT OR IGNORE INTO mail_participants (thread_id, user_id) VALUES (?, ?)", (thread_id, user_id))

            # messages
            cur.execute(
                """SELECT id, sender_id, body, created_at
                       FROM mail_messages WHERE thread_id=?
                       ORDER BY created_at ASC, id ASC""",
                (thread_id,),
            )
            mcols = [d[0] for d in cur.description]
            msgs = [dict(zip(mcols, row)) for row in cur.fetchall()]

            # mark read
            if mark_read and msgs:
                last_id = int(msgs[-1]["id"])
                cur.execute(
                    """UPDATE mail_participants SET last_read_message_id = ?
                           WHERE thread_id=? AND user_id=?""",
                    (last_id, thread_id, user_id),
                )

            # participants
            cur.execute("SELECT user_id FROM mail_participants WHERE thread_id=?", (thread_id,))
            participants = [int(r[0]) for r in cur.fetchall()]

            tcols = [d[0] for d in cur.description]
            return {"thread": {"id": t[0], "subject": t[1], "created_by": t[2], "created_at": t[3]},
                    "participants": participants, "messages": msgs}

    def unread_badge(self, user_id: int) -> Dict[str, int]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT SUM(CASE WHEN m.id > p.last_read_message_id AND m.sender_id != p.user_id
                       THEN 1 ELSE 0 END)
                       FROM mail_participants p
                       JOIN mail_messages m ON m.thread_id = p.thread_id
                       WHERE p.user_id = ?""",
                (user_id,),
            )
            mail_unread = int((cur.fetchone()[0] or 0))
        notif_unread = self.notifications.unread_count(user_id)
        return {"mail": mail_unread, "notifications": notif_unread}
