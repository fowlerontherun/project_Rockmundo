# File: backend/services/mail_service.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from services.notifications_service import NotificationsService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class MailError(Exception):
    pass

class MailService:
    def __init__(self, db_path: Optional[str] = None, notifications: Optional[NotificationsService] = None):
        self.db_path = str(db_path or DB_PATH)
        self.notifications = notifications or NotificationsService(db_path=self.db_path)

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # threads
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mail_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """)
            # messages
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mail_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(thread_id) REFERENCES mail_threads(id)
            )
            """)
            # participants per user
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mail_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                last_read_at TEXT,
                archived INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0,
                UNIQUE(thread_id, user_id),
                FOREIGN KEY(thread_id) REFERENCES mail_threads(id)
            )
            """)
            conn.commit()
        # ensure notifications schema too
        self.notifications.ensure_schema()

    # -------- Compose / Reply --------
    def start_thread(self, sender_id: int, recipient_ids: List[int], subject: str, body: str) -> int:
        if not recipient_ids:
            raise MailError("At least one recipient required")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute("INSERT INTO mail_threads (subject, created_by) VALUES (?, ?)", (subject, sender_id))
                thread_id = cur.lastrowid
                # add participants: sender + recipients
                participants = set(recipient_ids + [sender_id])
                for uid in participants:
                    cur.execute("""
                        INSERT OR IGNORE INTO mail_participants (thread_id, user_id, archived, deleted)
                        VALUES (?, ?, 0, 0)
                    """, (thread_id, uid))
                # first message
                cur.execute("""
                    INSERT INTO mail_messages (thread_id, sender_id, body)
                    VALUES (?, ?, ?)
                """, (thread_id, sender_id, body))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        # Notifications for recipients (exclude sender)
        for rid in recipient_ids:
            try:
                self.notifications.create_notification(
                    user_id=rid,
                    type="mail",
                    title=f"New message: {subject}",
                    body=body[:160],
                    link=f"/mail/thread/{thread_id}"
                )
            except Exception:
                # Don't fail mail delivery if notification fails
                pass

        return thread_id

    def reply(self, thread_id: int, sender_id: int, body: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # ensure thread exists
            cur.execute("SELECT subject FROM mail_threads WHERE id = ?", (thread_id,))
            row = cur.fetchone()
            if not row:
                raise MailError("Thread not found")
            subject = row[0]
            # insert reply
            cur.execute("""
                INSERT INTO mail_messages (thread_id, sender_id, body) VALUES (?, ?, ?)
            """, (thread_id, sender_id, body))
            msg_id = cur.lastrowid
            # ensure sender is participant
            cur.execute("""
                INSERT OR IGNORE INTO mail_participants (thread_id, user_id, archived, deleted)
                VALUES (?, ?, 0, 0)
            """, (thread_id, sender_id))
            conn.commit()

        # Notify all participants except sender
        recipients = self._participant_user_ids(thread_id, exclude_user_id=sender_id)
        for rid in recipients:
            try:
                self.notifications.create_notification(
                    user_id=rid,
                    type="mail",
                    title=f"New reply: {subject}",
                    body=body[:160],
                    link=f"/mail/thread/{thread_id}"
                )
            except Exception:
                pass

        return msg_id

    # -------- Queries --------
    def list_inbox(self, user_id: int, include_archived: bool = False, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            where = "mp.user_id = ? AND mp.deleted = 0"
            if not include_archived:
                where += " AND mp.archived = 0"
            cur.execute(f"""
                SELECT t.id AS thread_id, t.subject,
                       (SELECT MAX(m.created_at) FROM mail_messages m WHERE m.thread_id = t.id) AS last_message_at,
                       (SELECT COUNT(*) FROM mail_messages m WHERE m.thread_id = t.id AND (mp.last_read_at IS NULL OR m.created_at > mp.last_read_at)) AS unread_count
                FROM mail_threads t
                JOIN mail_participants mp ON mp.thread_id = t.id
                WHERE {where}
                ORDER BY last_message_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def list_sent(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id AS thread_id, t.subject,
                       (SELECT MAX(m.created_at) FROM mail_messages m WHERE m.thread_id = t.id) AS last_message_at
                FROM mail_threads t
                WHERE t.created_by = ?
                ORDER BY last_message_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def get_thread(self, thread_id: int, user_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # validate participant
            cur.execute("SELECT 1 FROM mail_participants WHERE thread_id = ? AND user_id = ? AND deleted = 0", (thread_id, user_id))
            if not cur.fetchone():
                raise MailError("Not a participant or thread deleted")
            # thread & messages
            cur.execute("SELECT * FROM mail_threads WHERE id = ?", (thread_id,))
            thread = dict(cur.fetchone())
            cur.execute("""
                SELECT id, sender_id, body, created_at
                FROM mail_messages
                WHERE thread_id = ?
                ORDER BY created_at ASC
            """, (thread_id,))
            messages = [dict(r) for r in cur.fetchall()]
            # participants
            cur.execute("SELECT user_id FROM mail_participants WHERE thread_id = ? AND deleted = 0", (thread_id,))
            participants = [int(r[0]) for r in cur.fetchall()]
            # mark read
            cur.execute("""
                UPDATE mail_participants
                SET last_read_at = datetime('now')
                WHERE thread_id = ? AND user_id = ?
            """, (thread_id, user_id))
            conn.commit()
            return {"thread": thread, "messages": messages, "participants": participants}

    def mark_read(self, thread_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE mail_participants
                SET last_read_at = datetime('now')
                WHERE thread_id = ? AND user_id = ?
            """, (thread_id, user_id))
            conn.commit()

    def archive(self, thread_id: int, user_id: int, archived: bool = True) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE mail_participants
                SET archived = ?
                WHERE thread_id = ? AND user_id = ?
            """, (1 if archived else 0, thread_id, user_id))
            conn.commit()

    def delete_for_user(self, thread_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE mail_participants
                SET deleted = 1
                WHERE thread_id = ? AND user_id = ?
            """, (thread_id, user_id))
            conn.commit()

    # -------- helpers --------
    def _participant_user_ids(self, thread_id: int, exclude_user_id: Optional[int] = None) -> List[int]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM mail_participants WHERE thread_id = ? AND deleted = 0", (thread_id,))
            ids = [int(r[0]) for r in cur.fetchall()]
        if exclude_user_id is not None:
            ids = [u for u in ids if u != exclude_user_id]
        return ids
