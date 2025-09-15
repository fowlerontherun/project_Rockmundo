import sqlite3
from datetime import datetime
from typing import Dict, Optional
from database import DB_PATH
from backend.services.song_service import SongService
from backend.services.song_popularity_service import song_popularity_service

class SongRemasterService:
    """Create remastered versions of songs and seed their popularity."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH
        self.song_service = SongService(db=self.db_path)

    def remaster_song(
        self,
        original_song_id: int,
        title_suffix: str = "(Remaster)",
        boost: int = 25,
    ) -> Dict[str, int]:
        """Create a remaster linked to ``original_song_id``.

        The original song's legacy_state is set to ``classic`` and a
        popularity boost is applied to the new remaster.
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT band_id, title, duration_sec, genre, license_fee, royalty_rate FROM songs WHERE id=?",
                (original_song_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Original song not found")
            band_id, title, duration_sec, genre, license_fee, royalty_rate = row

        new_title = f"{title} {title_suffix}".strip()
        data = {
            "band_id": band_id,
            "title": new_title,
            "duration_sec": duration_sec,
            "genre": genre,
            "royalties_split": {band_id: 100},
            "original_song_id": original_song_id,
            "license_fee": license_fee,
            "royalty_rate": royalty_rate,
            "legacy_state": "new",
            "original_release_date": datetime.utcnow().isoformat(),
        }
        new_song = self.song_service.create_song(data)
        new_id = new_song["song_id"]

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE songs SET legacy_state='classic' WHERE id=?", (original_song_id,))
            conn.commit()

        song_popularity_service.add_event(new_id, "remaster_release", boost)
        song_popularity_service.add_event(original_song_id, "legacy_classic", 0)
        return {"original_song_id": original_song_id, "remaster_id": new_id}


song_remaster_service = SongRemasterService()
