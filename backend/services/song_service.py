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
        license_fee = data.get("license_fee", 0)
        royalty_rate = data.get("royalty_rate", 0.0)

        if sum(royalties_split.values()) != 100:
            raise ValueError("Royalties must sum to 100%")

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO songs (band_id, title, duration_sec, genre, play_count, original_song_id, license_fee, royalty_rate)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (band_id, title, duration_sec, genre, original_song_id, license_fee, royalty_rate),
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
            SELECT id, title, duration_sec, genre, play_count, original_song_id, license_fee, royalty_rate
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
                    ["song_id", "title", "duration", "genre", "plays", "original_song_id", "license_fee", "royalty_rate"],
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

    # ------------------------------------------------------------------
    # Cover licensing and royalties
    # ------------------------------------------------------------------
    def has_active_license(self, song_id: int, band_id: int) -> bool:
        """Check if a band has an active license for a song."""
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM cover_royalties
            WHERE song_id = ? AND cover_band_id = ? AND license_proof_url IS NOT NULL
            LIMIT 1
            """,
            (song_id, band_id),
        )
        row = cur.fetchone()
        conn.close()
        return row is not None

    def purchase_cover_license(self, song_id: int, band_id: int, proof_url: str) -> Dict:
        """Record payment of the cover license fee and store proof."""
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT license_fee FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Song not found")
        fee = row[0]
        cur.execute(
            """
            INSERT INTO cover_royalties (song_id, cover_band_id, amount_owed, amount_paid, license_proof_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (song_id, band_id, fee, fee, proof_url),
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "license_fee": fee}

    def record_cover_usage(self, song_id: int, band_id: int, revenue_cents: int = 0) -> Dict:
        """Record a cover performance or recording and calculate royalties owed."""
        if not self.has_active_license(song_id, band_id):
            raise PermissionError("No active license for this cover")
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT royalty_rate FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Song not found")
        rate = row[0]
        owed = int(revenue_cents * rate)
        cur.execute(
            """
            INSERT INTO cover_royalties (song_id, cover_band_id, amount_owed, amount_paid)
            VALUES (?, ?, ?, 0)
            """,
            (song_id, band_id, owed),
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "amount_owed": owed}
