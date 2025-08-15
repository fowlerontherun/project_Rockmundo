import sqlite3
from backend.database import DB_PATH


def create_song(band_id: int, title: str, duration_sec: int, genre: str, royalties_split: dict) -> dict:
    if sum(royalties_split.values()) != 100:
        return {"error": "Royalties must sum to 100%"}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO songs (band_id, title, duration_sec, genre, play_count)
        VALUES (?, ?, ?, ?, 0)
    """, (band_id, title, duration_sec, genre))
    song_id = cur.lastrowid

    for user_id, percent in royalties_split.items():
        cur.execute("""
            INSERT INTO royalties (song_id, user_id, percent)
            VALUES (?, ?, ?)
        """, (song_id, user_id, percent))

    conn.commit()
    conn.close()
    return {"status": "ok", "song_id": song_id}


def get_songs_by_band(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, duration_sec, genre, play_count
        FROM songs
        WHERE band_id = ?
        ORDER BY id DESC
    """, (band_id,))
    songs = cur.fetchall()
    conn.close()

    return [dict(zip(["song_id", "title", "duration", "genre", "plays"], row)) for row in songs]


def update_song(song_id: int, updates: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for field, value in updates.items():
        cur.execute(f"UPDATE songs SET {field} = ? WHERE id = ?", (value, song_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Song updated"}


def delete_song(song_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM royalties WHERE song_id = ?", (song_id,))
    cur.execute("DELETE FROM album_songs WHERE song_id = ?", (song_id,))
    cur.execute("DELETE FROM songs WHERE id = ?", (song_id,))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Song deleted"}