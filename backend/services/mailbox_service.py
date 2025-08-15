import sqlite3
from datetime import datetime
from backend.database import DB_PATH

def send_message(sender_id: int, receiver_id: int, subject: str, body: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, subject, body, sent_at, read, deleted)
        VALUES (?, ?, ?, ?, ?, 0, 0)
    """, (sender_id, receiver_id, subject, body, datetime.utcnow().isoformat()))
    message_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "ok", "message_id": message_id}

def get_inbox(user_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sender_id, subject, body, sent_at, read
        FROM messages
        WHERE receiver_id = ? AND deleted = 0
        ORDER BY sent_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["message_id", "sender_id", "subject", "body", "sent_at", "read"], row)) for row in rows]

def get_sent(user_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, receiver_id, subject, body, sent_at
        FROM messages
        WHERE sender_id = ? AND deleted = 0
        ORDER BY sent_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["message_id", "receiver_id", "subject", "body", "sent_at"], row)) for row in rows]

def mark_as_read(message_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE messages SET read = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Message marked as read"}

def delete_message(message_id: int, user_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Soft delete: only allow sender or receiver to delete
    cur.execute("""
        UPDATE messages
        SET deleted = 1
        WHERE id = ? AND (sender_id = ? OR receiver_id = ?)
    """, (message_id, user_id, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Message deleted"}