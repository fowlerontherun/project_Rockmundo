import sqlite3
from datetime import datetime
from backend.database import DB_PATH


def stream_song(user_id: int, song_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Record stream
    cur.execute("""
        INSERT INTO streams (user_id, song_id, timestamp)
        VALUES (?, ?, ?)
    """, (user_id, song_id, datetime.now()))

    # Increment play count
    cur.execute("""
        UPDATE songs
        SET play_count = play_count + 1
        WHERE id = ?
    """, (song_id,))

    # Simulate revenue (e.g., $0.003 per stream)
    revenue = 0.003
    cur.execute("""
        SELECT user_id, percent FROM royalties WHERE song_id = ?
    """, (song_id,))
    royalty_rows = cur.fetchall()

    for row in royalty_rows:
        receiver_id, percent = row
        amount = revenue * (percent / 100)
        cur.execute("""
            INSERT INTO earnings (user_id, source_type, source_id, amount, timestamp)
            VALUES (?, 'stream', ?, ?, ?)
        """, (receiver_id, song_id, amount, datetime.now()))

    conn.commit()
    conn.close()

    return {"status": "ok", "revenue": round(revenue, 4)}


def get_stream_count(song_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM streams WHERE song_id = ?", (song_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def calculate_stream_revenue(song_id: int) -> float:
    total_streams = get_stream_count(song_id)
    return round(total_streams * 0.003, 2)


def list_top_streamed_songs(limit=10) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.title, s.play_count, b.name
        FROM songs s
        JOIN bands b ON s.band_id = b.id
        ORDER BY s.play_count DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [dict(zip(["song_id", "title", "play_count", "band_name"], row)) for row in rows]


def get_user_stream_history(user_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.title, str.timestamp
        FROM streams str
        JOIN songs s ON str.song_id = s.id
        WHERE str.user_id = ?
        ORDER BY str.timestamp DESC
        LIMIT 50
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["song_title", "timestamp"], row)) for row in rows]