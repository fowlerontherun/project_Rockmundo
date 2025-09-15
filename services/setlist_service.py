import json
import sqlite3
from database import DB_PATH


def create_revision(setlist_id: int, setlist, author: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO setlist_revisions (setlist_id, setlist, author) VALUES (?, ?, ?)",
        (setlist_id, json.dumps(setlist), author),
    )
    revision_id = cur.lastrowid
    conn.commit()
    conn.close()
    return revision_id


def approve_revision(setlist_id: int, revision_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE setlist_revisions SET approved = 1 WHERE id = ? AND setlist_id = ?",
        (revision_id, setlist_id),
    )
    updated = cur.rowcount
    if updated:
        cur.execute(
            "UPDATE setlist_revisions SET approved = 0 WHERE setlist_id = ? AND id <> ?",
            (setlist_id, revision_id),
        )
    conn.commit()
    conn.close()
    return bool(updated)


def list_revisions(setlist_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, setlist, author, created_at, approved FROM setlist_revisions WHERE setlist_id = ? ORDER BY created_at DESC",
        (setlist_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "setlist": json.loads(r[1]),
            "author": r[2],
            "created_at": r[3],
            "approved": bool(r[4]),
        }
        for r in rows
    ]


def get_approved_setlist(revision_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT setlist FROM setlist_revisions WHERE id = ? AND approved = 1",
        (revision_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None
