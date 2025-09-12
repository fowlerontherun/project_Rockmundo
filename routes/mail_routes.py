"""Mail API routes.

Endpoints for sending, listing, and deleting mail messages.
"""

import sqlite3

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.auth.dependencies import get_current_user_id
from services.mailbox_service import delete_message, get_inbox, send_message
from services.storage_service import save_attachment
from utils.db import aget_conn


router = APIRouter(prefix="/mail", tags=["Mail"])


@router.post("/")
async def send_mail(
    recipient_id: int = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    files: list[UploadFile] = File([]),
    user_id: int = Depends(get_current_user_id),
):
    """Send a mail message from the authenticated user."""
    attachments = [await save_attachment(f) for f in files]
    return await send_message(user_id, recipient_id, subject, body, attachments)


@router.get("/")
async def list_mail(user_id: int = Depends(get_current_user_id)):
    """Return the inbox for the authenticated user."""
    return await get_inbox(user_id)


@router.delete("/{message_id}")
async def delete_mail(message_id: int, user_id: int = Depends(get_current_user_id)):
    """Delete a mail message owned by the authenticated user."""
    return await delete_message(message_id, user_id)


@router.get("/search")
async def search_mail(
    q: str = "",
    user_id: int = Depends(get_current_user_id),
):
    """Search mail messages using full-text search.

    Falls back to a simple LIKE query if the FTS virtual table is
    unavailable.  An empty query returns an empty list immediately.
    """

    query = q.strip()
    if not query:
        return []

    async with aget_conn() as conn:
        try:
            cur = await conn.execute(
                """
                SELECT mm.id, mm.thread_id, mm.body
                FROM mail_fts mf
                JOIN mail_messages mm ON mm.id = mf.rowid
                JOIN mail_participants mp ON mp.thread_id = mm.thread_id
                WHERE mp.user_id = ? AND mail_fts MATCH ?
                ORDER BY mm.created_at DESC
                LIMIT 20
                """,
                (user_id, f"{query}*"),
            )
            rows = await cur.fetchall()
        except sqlite3.OperationalError:
            like = f"%{query}%"
            cur = await conn.execute(
                """
                SELECT mm.id, mm.thread_id, mm.body
                FROM mail_messages mm
                JOIN mail_participants mp ON mp.thread_id = mm.thread_id
                WHERE mp.user_id = ? AND mm.body LIKE ?
                ORDER BY mm.created_at DESC
                LIMIT 20
                """,
                (user_id, like),
            )
            rows = await cur.fetchall()

    return [
        {
            "message_id": row["id"],
            "thread_id": row["thread_id"],
            "body": row["body"],
        }
        for row in rows
    ]

