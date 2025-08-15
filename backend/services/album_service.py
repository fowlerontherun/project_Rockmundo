import sqlite3
from datetime import datetime
from backend.database import DB_PATH
from backend.services import band_service


def create_album(band_id: int, title: str, album_type: str, song_ids: list, shared_with_band_id=None) -> dict:
    if album_type == "EP" and len(song_ids) > 4:
        return {"error": "EPs cannot contain more than 4 songs"}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO albums (band_id, title, album_type, shared_with_band_id, release_date)
        VALUES (?, ?, ?, ?, NULL)
    """, (band_id, title, album_type, shared_with_band_id))
    album_id = cur.lastrowid

    # Link songs to album
    for song_id in song_ids:
        cur.execute("""
            INSERT INTO album_songs (album_id, song_id)
            VALUES (?, ?)
        """, (album_id, song_id))

    conn.commit()
    conn.close()

    return {"status": "ok", "album_id": album_id}


def get_albums_by_band(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, album_type, release_date, shared_with_band_id
        FROM albums
        WHERE band_id = ?
        ORDER BY release_date DESC NULLS LAST
    """, (band_id,))
    albums = cur.fetchall()
    conn.close()

    return [dict(zip(["album_id", "title", "type", "release_date", "collab_band_id"], row)) for row in albums]


def update_album(album_id: int, updates: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for field, value in updates.items():
        cur.execute(f"UPDATE albums SET {field} = ? WHERE id = ?", (value, album_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Album updated"}


def publish_album(album_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    release_date = datetime.now().date()
    cur.execute("UPDATE albums SET release_date = ? WHERE id = ?", (release_date, album_id))

    # Fame and revenue gain simulation
    cur.execute("""
        SELECT band_id, shared_with_band_id FROM albums WHERE id = ?
    """, (album_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "Album not found"}

    band_id, collab_id = row
    fame_gain = 50
    revenue = 1000

    earnings = band_service.split_earnings(band_id, revenue, collab_id)

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "release_date": str(release_date),
        "fame_gain": fame_gain,
        "revenue": revenue,
        "earnings": earnings
    }