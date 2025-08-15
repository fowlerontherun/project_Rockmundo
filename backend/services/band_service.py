import sqlite3
from backend.database import DB_PATH


def create_band(user_id: int, band_name: str, genre: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bands (name, genre, founder_user_id, fame)
        VALUES (?, ?, ?, 0)
    """, (band_name, genre, user_id))
    band_id = cur.lastrowid

    # Add founder as first member
    cur.execute("""
        INSERT INTO band_members (band_id, user_id, role)
        VALUES (?, ?, ?)
    """, (band_id, user_id, "founder"))

    conn.commit()
    conn.close()
    return {"status": "ok", "band_id": band_id}


def add_member(band_id: int, user_id: int, role: str = "member") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO band_members (band_id, user_id, role)
        VALUES (?, ?, ?)
    """, (band_id, user_id, role))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Member added"}


def remove_member(band_id: int, user_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM band_members WHERE band_id = ? AND user_id = ?
    """, (band_id, user_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Member removed"}


def get_band_info(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, genre, fame FROM bands WHERE id = ?
    """, (band_id,))
    band = cur.fetchone()

    cur.execute("""
        SELECT user_id, role FROM band_members WHERE band_id = ?
    """, (band_id,))
    members = cur.fetchall()

    conn.close()
    return {
        "name": band[0],
        "genre": band[1],
        "fame": band[2],
        "members": [dict(zip(["user_id", "role"], m)) for m in members]
    }


def split_earnings(band_id: int, amount: int, collaboration_band_id: int = None) -> dict:
    if collaboration_band_id:
        # 50/50 revenue split
        return {
            "band_1_share": amount // 2,
            "band_2_share": amount - (amount // 2)
        }

    # Normal case: split among members equally
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id FROM band_members WHERE band_id = ?
    """, (band_id,))
    members = [r[0] for r in cur.fetchall()]
    num_members = len(members)
    share = amount // num_members if num_members else 0

    payouts = {uid: share for uid in members}
    conn.close()

    return {
        "total": amount,
        "per_member": share,
        "payouts": payouts
    }


def get_band_collaborations(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, release_date, shared_with_band_id
        FROM albums
        WHERE band_id = ? AND shared_with_band_id IS NOT NULL
    """, (band_id,))
    collabs = cur.fetchall()
    conn.close()

    return [
        dict(zip(["album_id", "title", "release_date", "collab_band_id"], row))
        for row in collabs
    ]