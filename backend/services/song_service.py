import sqlite3
from datetime import datetime
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
        legacy_state = data.get("legacy_state", "new")
        original_release_date = data.get("original_release_date") or datetime.utcnow().isoformat()

        if sum(royalties_split.values()) != 100:
            raise ValueError("Royalties must sum to 100%")

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO songs (
                band_id, title, duration_sec, genre, play_count,
                original_song_id, license_fee, royalty_rate, legacy_state, original_release_date
            )
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
            """,
            (
                band_id,
                title,
                duration_sec,
                genre,
                original_song_id,
                license_fee,
                royalty_rate,
                legacy_state,
                original_release_date,
            ),
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
            SELECT id, title, duration_sec, genre, play_count, original_song_id, license_fee, royalty_rate, legacy_state, original_release_date
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
                    [
                        "song_id",
                        "title",
                        "duration",
                        "genre",
                        "plays",
                        "original_song_id",
                        "license_fee",
                        "royalty_rate",
                        "legacy_state",
                        "original_release_date",
                    ],
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
    def purchase_cover_license(
        self,
        song_id: int,
        band_id: int,
        proof_url: str,
        duration_days: int = 365,
    ) -> Dict:
        """Record payment of the cover license fee and store proof.

        A record is inserted into ``cover_license_transactions`` with the
        purchase timestamp and an expiration date.  The returned dictionary
        includes the transaction id so it can be referenced when creating the
        cover song.
        """

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
            INSERT INTO cover_license_transactions
            (song_id, cover_band_id, license_fee, license_proof_url, purchased_at, expires_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now', ?))
            """,
            (song_id, band_id, fee, proof_url, f'+{duration_days} days'),
        )
        tx_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"status": "ok", "license_fee": fee, "transaction_id": tx_id}

    def has_active_license(self, song_id: int, band_id: int) -> bool:
        """Check if a band has an active (unexpired) license for a song."""

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM cover_license_transactions
            WHERE song_id = ? AND cover_band_id = ? AND expires_at > datetime('now')
            LIMIT 1
            """,
            (song_id, band_id),
        )
        row = cur.fetchone()
        conn.close()
        return row is not None

    def create_cover(self, data: Dict, license_transaction_id: int) -> Dict:
        """Create a cover song ensuring the license transaction is valid."""

        band_id = data["band_id"]
        original_song_id = data.get("original_song_id")
        if not original_song_id:
            raise ValueError("original_song_id is required for a cover")

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT song_id, cover_band_id, expires_at
            FROM cover_license_transactions
            WHERE id = ?
            """,
            (license_transaction_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row or row[0] != original_song_id or row[1] != band_id:
            raise PermissionError("Invalid license transaction")
        expires_at = row[2]
        conn_exp = sqlite3.connect(self.db)
        cur_exp = conn_exp.cursor()
        cur_exp.execute("SELECT datetime(?) > datetime('now')", (expires_at,))
        valid = cur_exp.fetchone()[0]
        conn_exp.close()
        if not valid:
            raise PermissionError("License has expired")

        return self.create_song(data)

    def record_cover_usage(self, song_id: int, band_id: int, revenue_cents: int = 0) -> Dict:
        """Record a cover performance or recording and calculate royalties owed.

        ``revenue_cents`` represents the revenue generated by the cover. The
        royalty owed is ``revenue_cents * royalty_rate`` for the original song
        owner.  Each call stores a transaction in ``cover_royalties`` so the
        band can review outstanding payments.
        """

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

    def list_cover_royalties(self, band_id: int) -> List[Dict]:
        """List cover royalty transactions for ``band_id``."""
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT song_id, amount_owed, amount_paid
            FROM cover_royalties
            WHERE cover_band_id = ?
            ORDER BY id DESC
            """,
            (band_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            dict(zip(["song_id", "amount_owed", "amount_paid"], row))
            for row in rows
        ]
