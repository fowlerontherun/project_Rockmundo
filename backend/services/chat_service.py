import sqlite3
from datetime import datetime


# TODO: Replace in-memory stores with persistent storage to avoid data loss on
# restart.
chat_store: dict[int, list] = {}
group_chat_store: dict[int, list] = {}
group_members: dict[int, set[int]] = {}
# Registry to track which groups a user belongs to
user_groups: dict[int, set[int]] = {}
from backend.database import DB_PATH



def _ensure_tables() -> None:
    """Create chat tables if they do not yet exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS direct_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (group_id, user_id)
            )
            """
        )
        conn.commit()

    if user_id not in user_groups:
        user_groups[user_id] = set()
    user_groups[user_id].add(group_id)


def add_user_to_group(group_id: str, user_id: int) -> None:
    _ensure_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, user_id),
        )
        conn.commit()


def remove_user_from_group(group_id: str, user_id: int) -> None:
    _ensure_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM group_members WHERE group_id=? AND user_id=?",
            (group_id, user_id),
        )
        conn.commit()


def send_message(data: dict) -> dict:
    _ensure_tables()
    sender = data["sender_id"]
    recipient = data["recipient_id"]
    timestamp = str(datetime.utcnow())
    message = {
        "sender_id": sender,
        "recipient_id": recipient,
        "content": data["content"],
        "timestamp": timestamp,
    }

    chat_store.setdefault(recipient, []).append(message)
    chat_store.setdefault(sender, []).append(message)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO direct_messages (sender_id, recipient_id, content, timestamp)"
            " VALUES (?, ?, ?, ?)",
            (sender, recipient, data["content"], timestamp),
        )
        conn.commit()

    return {"status": "message_sent", "message": message}


def send_group_chat(data: dict) -> dict:
    _ensure_tables()
    group_id = data["group_id"]
    add_user_to_group(group_id, data["sender_id"])
    timestamp = str(datetime.utcnow())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO group_messages (group_id, sender_id, content, timestamp)"
            " VALUES (?, ?, ?, ?)",
            (group_id, data["sender_id"], data["content"], timestamp),
        )
        conn.commit()
    return {"status": "group_message_sent"}



def get_user_chat_history(user_id):
    groups = user_groups.get(user_id, set())
    return {
        "direct_messages": chat_store.get(user_id, []),
        "group_chats": {gid: group_chat_store.get(gid, []) for gid in groups},
    }

def get_user_chat_history(user_id: int) -> dict:
    _ensure_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT sender_id, recipient_id, content, timestamp FROM direct_messages"
            " WHERE sender_id=? OR recipient_id=? ORDER BY id",
            (user_id, user_id),
        )
        direct_messages = [dict(row) for row in cur.fetchall()]

        cur = conn.execute(
            "SELECT group_id FROM group_members WHERE user_id=?",
            (user_id,),
        )
        group_ids = [row["group_id"] for row in cur.fetchall()]
        group_chats = {}
        for gid in group_ids:
            cur = conn.execute(
                "SELECT sender_id, content, timestamp FROM group_messages"
                " WHERE group_id=? ORDER BY id",
                (gid,),
            )
            group_chats[gid] = [dict(row) for row in cur.fetchall()]

    return {"direct_messages": direct_messages, "group_chats": group_chats}


