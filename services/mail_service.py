from __future__ import annotations

import mimetypes
import os
import time
import uuid
from typing import Dict, List, Optional

from services.notifications_service import NotificationsService
from services.storage_service import get_storage_backend
from utils.db import get_conn


class MailService:
    """Minimal mail service supporting compose and unread badge."""

    def __init__(self, *, db_path: Optional[str] = None, notifications: NotificationsService | None = None):
        self.db_path = db_path
        self.notifications = notifications or NotificationsService(db_path=db_path)

    def compose(
        self,
        *,
        sender_id: int,
        recipient_ids: List[int],
        subject: str,
        body: str,
    ) -> Dict[str, int]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO mail_threads (subject, created_by) VALUES (?, ?)",
                (subject, sender_id),
            )
            thread_id = int(cur.lastrowid)
            cur.execute(
                "INSERT INTO mail_messages (thread_id, sender_id, body) VALUES (?, ?, ?)",
                (thread_id, sender_id, body),
            )
            message_id = int(cur.lastrowid)

            participants = set(recipient_ids + [sender_id])
            for uid in participants:
                cur.execute(
                    "INSERT INTO mail_participants (thread_id, user_id, last_read_message_id) VALUES (?, ?, ?)",
                    (thread_id, uid, message_id if uid == sender_id else 0),
                )
            conn.commit()

        for uid in recipient_ids:
            self.notifications.create(user_id=uid, title=subject, body=body, type_="mail")

        return {"thread_id": thread_id, "message_id": message_id}

    def unread_badge(self, user_id: int) -> Dict[str, int]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) FROM mail_participants mp
                JOIN mail_messages mm ON mm.thread_id = mp.thread_id
                WHERE mp.user_id = ? AND mm.id > mp.last_read_message_id
                """,
                (user_id,),
            )
            mail_count = int(cur.fetchone()[0])
        notif_count = self.notifications.unread_count(user_id)
        return {"mail": mail_count, "notifications": notif_count}


# === Storage-backed attachment functions ===

def _guess_mime(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _attachment_key(message_id: int, filename: str) -> str:
    safe = filename.replace("..", "").replace("/", "_").replace("\\", "_")
    return f"mail/attachments/{message_id}/{int(time.time())}_{uuid.uuid4().hex}_{safe}"


def add_attachment_from_path(
    message_id: int,
    file_path: str,
    filename: str | None = None,
    content_type: str | None = None,
):
    storage = get_storage_backend()
    filename = filename or os.path.basename(file_path)
    content_type = content_type or _guess_mime(filename)
    key = _attachment_key(message_id, filename)
    obj = storage.upload_file(file_path, key, content_type=content_type)
    return {
        "message_id": message_id,
        "filename": filename,
        "mime": obj.content_type or content_type,
        "size": obj.size,
        "storage_url": obj.url,
        "storage_key": obj.key,
    }


def add_attachment_from_bytes(
    message_id: int,
    data: bytes,
    filename: str,
    content_type: str | None = None,
):
    storage = get_storage_backend()
    content_type = content_type or _guess_mime(filename)
    key = _attachment_key(message_id, filename)
    obj = storage.upload_bytes(data, key, content_type=content_type)
    return {
        "message_id": message_id,
        "filename": filename,
        "mime": obj.content_type or content_type,
        "size": obj.size,
        "storage_url": obj.url,
        "storage_key": obj.key,
    }


def delete_attachment(storage_key: str) -> None:
    storage = get_storage_backend()
    storage.delete(storage_key)
