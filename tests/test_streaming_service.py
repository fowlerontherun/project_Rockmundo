import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))
from backend import database  # noqa: E402


def _setup_db(tmp_path):
    db = tmp_path / "streaming.sqlite"
    database.DB_PATH = str(db)

    import backend.services.song_popularity_service as sps
    import backend.services.streaming_service as ss
    sps.DB_PATH = str(db)
    ss.DB_PATH = str(db)

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            play_count INTEGER DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            song_id INTEGER,
            timestamp TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE royalties (
            song_id INTEGER,
            user_id INTEGER,
            percent REAL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            source_type TEXT,
            source_id INTEGER,
            amount REAL,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return ss


@pytest.mark.asyncio
async def test_stream_song_revenue_and_play_counts(tmp_path):
    streaming_service = _setup_db(tmp_path)

    conn = sqlite3.connect(database.DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO songs (id, title, play_count) VALUES (1, 'Song A', 0)")
    cur.executemany(
        "INSERT INTO royalties (song_id, user_id, percent) VALUES (1, ?, ?)",
        [(10, 60), (20, 40)],
    )
    conn.commit()
    conn.close()

    result = await streaming_service.stream_song(user_id=5, song_id=1)
    assert result == {"status": "ok", "revenue": 0.003}

    conn = sqlite3.connect(database.DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT play_count FROM songs WHERE id = 1")
    play_count = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM streams WHERE song_id = 1 AND user_id = 5"
    )
    stream_count = cur.fetchone()[0]
    cur.execute(
        "SELECT user_id, amount FROM earnings WHERE source_type = 'stream' AND source_id = 1 ORDER BY user_id"
    )
    earnings = cur.fetchall()
    conn.close()

    assert play_count == 1
    assert stream_count == 1
    assert earnings[0][0] == 10
    assert earnings[1][0] == 20
    assert earnings[0][1] == pytest.approx(0.0018)
    assert earnings[1][1] == pytest.approx(0.0012)
