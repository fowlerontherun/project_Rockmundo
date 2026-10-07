from datetime import datetime
from typing import Dict, List

from database import DB_PATH
from utils.db import aget_conn


async def send_message(
    sender_id: int,
    receiver_id: int,
    subject: str,
    body: str,
    attachments: List[Dict[str, str]] | None = None,
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

        if attachments:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mail_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    url TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
                )
                """
            )
            await conn.executemany(
                "INSERT INTO mail_attachments (message_id, filename, url) VALUES (?, ?, ?)",
                [(message_id, att["filename"], att["url"]) for att in attachments],
            )

    return {"status": "ok", "message_id": message_id}


async def get_inbox(user_id: int) -> List[Dict[str, object]]:
    """Return the user's thread-based inbox.

    The current RockMundo mail schema stores subjects on `mail_threads` and
    bodies on `mail_messages`. Older code queried a removed `messages`
    table, which meant MailService-created system inbox items were invisible.
    """
    async with aget_conn(DB_PATH) as conn:
        cur = await conn.execute(
            """
            SELECT
                mm.id AS message_id,
                mt.id AS thread_id,
                mm.sender_id,
                mt.subject,
                mm.body,
                mm.created_at,
                mp.last_read_message_id
            FROM mail_participants mp
            JOIN mail_threads mt ON mt.id = mp.thread_id
            JOIN mail_messages mm ON mm.thread_id = mt.id
            WHERE mp.user_id = ?
              AND mm.id = (
                  SELECT MAX(mm2.id)
                  FROM mail_messages mm2
                  WHERE mm2.thread_id = mt.id
              )
            ORDER BY mm.created_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()

    return [
        {
            "message_id": row["message_id"],
            "thread_id": row["thread_id"],
            "sender_id": row["sender_id"],
            "subject": row["subject"],
            "body": row["body"],
            "sent_at": row["created_at"],
            "read": int(row["message_id"] <= (row["last_read_message_id"] or 0)),
            "attachments": [],
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

        attachments_map: Dict[int, List[Dict[str, str]]] = {}
        check = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mail_attachments'"
        )
        if await check.fetchone():
            cur = await conn.execute(
                "SELECT message_id, filename, url FROM mail_attachments WHERE message_id IN ({seq})".format(
                    seq=",".join(str(r[0]) for r in rows) or "0"
                )
            )
            for msg_id, filename, url in await cur.fetchall():
                attachments_map.setdefault(msg_id, []).append({"filename": filename, "url": url})

    return [
        {
            "message_id": row[0],
            "receiver_id": row[1],
            "subject": row[2],
            "body": row[3],
            "sent_at": row[4],
            "attachments": attachments_map.get(row[0], []),
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

