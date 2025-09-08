from datetime import datetime
from typing import Dict, List

from backend.database import DB_PATH
from utils.db import aget_conn


async def send_message(
    sender_id: int, receiver_id: int, subject: str, body: str
) -> Dict[str, int | str]:
    async with aget_conn(DB_PATH) as conn:
        cur = await conn.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, subject, body, sent_at, read, deleted)
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """,
            (sender_id, receiver_id, subject, body, datetime.utcnow().isoformat()),
        )
        message_id = cur.lastrowid
    return {"status": "ok", "message_id": message_id}


async def get_inbox(user_id: int) -> List[Dict[str, object]]:
    async with aget_conn(DB_PATH) as conn:
        cur = await conn.execute(
            """
            SELECT id, sender_id, subject, body, sent_at, read
            FROM messages
            WHERE receiver_id = ? AND deleted = 0
            ORDER BY sent_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
    return [
        {
            "message_id": row[0],
            "sender_id": row[1],
            "subject": row[2],
            "body": row[3],
            "sent_at": row[4],
            "read": row[5],
        }
        for row in rows
    ]


async def get_sent(user_id: int) -> List[Dict[str, object]]:
    async with aget_conn(DB_PATH) as conn:
        cur = await conn.execute(
            """
            SELECT id, receiver_id, subject, body, sent_at
            FROM messages
            WHERE sender_id = ? AND deleted = 0
            ORDER BY sent_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
    return [
        {
            "message_id": row[0],
            "receiver_id": row[1],
            "subject": row[2],
            "body": row[3],
            "sent_at": row[4],
        }
        for row in rows
    ]


async def mark_as_read(message_id: int) -> Dict[str, str]:
    async with aget_conn(DB_PATH) as conn:
        await conn.execute("UPDATE messages SET read = 1 WHERE id = ?", (message_id,))
    return {"status": "ok", "message": "Message marked as read"}


async def delete_message(message_id: int, user_id: int) -> Dict[str, str]:
    async with aget_conn(DB_PATH) as conn:
        await conn.execute(
            """
            UPDATE messages
            SET deleted = 1
            WHERE id = ? AND (sender_id = ? OR receiver_id = ?)
            """,
            (message_id, user_id, user_id),
        )
    return {"status": "ok", "message": "Message deleted"}

