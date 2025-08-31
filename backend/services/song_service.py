import sqlite3
from typing import Dict, List, Optional

from backend.database import DB_PATH


class SongService:
    """Service layer for CRUD operations on songs.

    Supports creating cover songs via the ``original_song_id`` column and
    listing covers of a given song.
    """

    def __init__(self, db: Optional[str] = None) -> None:
        self.db = db or DB_PATH

    # ------------------------------------------------------------------
    # Creation and queries
    # ------------------------------------------------------------------
    def create_song(self, data: Dict) -> Dict:
        """Create a song.

        ``data`` should contain ``band_id``, ``title``, ``duration_sec`` and
        ``genre``.  ``royalties_split`` is optional and defaults to 100%% for the
        owning band.  ``original_song_id`` can be provided to mark the song as a
        cover of another song.
        """

        band_id = data["band_id"]
        title = data["title"]
        duration_sec = data["duration_sec"]
        genre = data["genre"]
        royalties_split = data.get("royalties_split", {band_id: 100})
        original_song_id = data.get("original_song_id")

        if sum(royalties_split.values()) != 100:
            raise ValueError("Royalties must sum to 100%")

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO songs (band_id, title, duration_sec, genre, play_count, original_song_id)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (band_id, title, duration_sec, genre, original_song_id),
        )
        song_id = cur.lastrowid

        for user_id, percent in royalties_split.items():
            cur.execute(
                """INSERT INTO royalties (song_id, user_id, percent) VALUES (?, ?, ?)""",
                (song_id, user_id, percent),
            )

        conn.commit()
        conn.close()
        return {"status": "ok", "song_id": song_id}

    def list_songs_by_band(self, band_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, duration_sec, genre, play_count, original_song_id
            FROM songs
            WHERE band_id = ?
            ORDER BY id DESC
            """,
            (band_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            dict(
                zip(
                    ["song_id", "title", "duration", "genre", "plays", "original_song_id"],
                    row,
                )
            )
            for row in rows
        ]

    def list_covers_of_song(self, song_id: int) -> List[Dict]:
        """Return cover versions referencing ``song_id`` as original."""
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, band_id, title FROM songs WHERE original_song_id = ?",
            (song_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(zip(["song_id", "band_id", "title"], row)) for row in rows]

    # ------------------------------------------------------------------
    # Updates and deletion
    # ------------------------------------------------------------------
    def update_song(self, song_id: int, updates: Dict) -> Dict:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        for field, value in updates.items():
            cur.execute(f"UPDATE songs SET {field} = ? WHERE id = ?", (value, song_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Song updated"}

    def delete_song(self, song_id: int) -> Dict:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("DELETE FROM royalties WHERE song_id = ?", (song_id,))
        cur.execute("DELETE FROM album_songs WHERE song_id = ?", (song_id,))
        cur.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Song deleted"}
