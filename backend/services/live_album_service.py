import asyncio
import json
import sqlite3
from typing import Dict, List

from models.album import Album

from backend.database import DB_PATH
from backend.services import audio_mixing_service
from backend.services.ai_art_service import ai_art_service


class LiveAlbumService:
    """Compile and edit live albums from existing performance recordings."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or str(DB_PATH)
        # ``_albums`` keeps in-memory drafts keyed by album id so callers can
        # reorder or remove tracks before a release is finalized.  The data is
        # transient and primarily used by the tests.
        self._albums: Dict[int, Dict] = {}
        self._next_id = 1

    def compile_live_album(self, performance_ids: List[int], title: str) -> Dict:
        if len(performance_ids) != 5:
            raise ValueError("Exactly five performance IDs are required")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        performances = []
        cities = set()
        venues = set()
        for pid in performance_ids:
            cur.execute(
                "SELECT rowid, band_id, city, venue, setlist, skill_gain FROM live_performances WHERE rowid = ?",
                (pid,),
            )
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError(f"Performance {pid} not found")
            rowid, band_id, city, venue, setlist_json, skill_gain = row
            setlist_data = json.loads(setlist_json)
            actions = setlist_data.get("setlist", []) + setlist_data.get("encore", [])
            songs: List[int] = []
            for action in actions:
                if action.get("type") in ("song", "encore"):
                    ref = action.get("reference")
                    try:
                        songs.append(int(ref))
                    except (TypeError, ValueError):
                        continue
            cur.execute(
                "SELECT song_id, performance_score FROM recorded_tracks WHERE performance_id = ?",
                (pid,),
            )
            song_scores = {sid: score for sid, score in cur.fetchall()}
            performances.append(
                {
                    "id": rowid,
                    "band_id": band_id,
                    "songs": songs,
                    "order": songs,
                    "song_scores": song_scores,
                    "skill_gain": skill_gain,
                    "city": city,
                    "venue": venue,
                }
            )
            if city:
                cities.add(city)
            if venue:
                venues.add(venue)
        conn.close()
        band_ids = {p["band_id"] for p in performances}
        if len(band_ids) != 1:
            raise ValueError("All performances must belong to the same band")
        common = set(performances[0]["songs"])
        for p in performances[1:]:
            common &= set(p["songs"])
        if not common:
            raise ValueError("No common songs across performances")
        order = [s for s in performances[0]["order"] if s in common]
        songs: List[dict] = []
        tracks: List[dict] = []
        for song_id in order:
            best = max(
                (p for p in performances if song_id in p["songs"]),
                key=lambda p: p["song_scores"].get(song_id, p["skill_gain"]),
            )
            score = best["song_scores"].get(song_id, best["skill_gain"])
            songs.append(
                {
                    "song_id": song_id,
                    "show_id": best["id"],
                    "performance_score": score,
                }
            )
            tracks.append(
                {
                    "song_id": song_id,
                    "performance_id": best["id"],
                    "performance_score": score,
                }
            )

        # Mix the selected performances to produce final track identifiers
        mixed_ids = audio_mixing_service.mix_tracks(
            [t["performance_id"] for t in tracks]
        )
        for track, mixed_id in zip(tracks, mixed_ids):
            track["track_id"] = mixed_id
            del track["performance_id"]

        themes = list(cities | venues)
        try:
            cover_url = asyncio.run(
                ai_art_service.generate_album_art(title, themes)
            )
        except Exception:
            cover_url = None

        album = Album(
            id=0,
            title=title,
            album_type="live",
            genre_id=0,
            band_id=performances[0]["band_id"],
            songs=songs,
            cover_art=cover_url,
        )

        data = album.to_dict()
        data["tracks"] = tracks
        data["song_ids"] = [s["song_id"] for s in songs]

        # Store a draft so it can be edited prior to publishing.  ``Album``
        # objects use ``id`` for persistence; for drafts we assign a simple
        # incremental identifier.
        album_id = self._next_id
        self._next_id += 1
        data["id"] = album_id
        self._albums[album_id] = data

        return data

    # ------------------------------------------------------------------
    def update_tracks(self, album_id: int, new_order: List[int]) -> Dict:
        """Reorder or remove tracks for a drafted live album.

        ``new_order`` is a list of song IDs representing the desired order.  It
        must be a subset of the current songs.  Removed songs are validated to
        ensure they haven't been released as singles or EPs.
        """

        album = self._albums.get(album_id)
        if not album:
            raise ValueError("Album not found")

        current_song_ids = [t["song_id"] for t in album["tracks"]]
        unknown = set(new_order) - set(current_song_ids)
        if unknown:
            raise ValueError(f"Unknown songs in order: {sorted(unknown)}")

        removed = [sid for sid in current_song_ids if sid not in new_order]
        if removed:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            for sid in removed:
                try:
                    cur.execute(
                        """
                        SELECT r.format FROM releases r
                        JOIN release_tracks rt ON r.id = rt.release_id
                        WHERE rt.song_id = ? AND r.format IN ('single', 'ep')
                        """,
                        (sid,),
                    )
                except sqlite3.OperationalError:
                    # ``releases`` tables may not exist in every database; in
                    # that case we treat the track as unreleased.
                    continue
                if cur.fetchone():
                    conn.close()
                    raise ValueError(
                        f"Track {sid} already released as single/EP"
                    )
            conn.close()

        # Rebuild track list in the requested order
        track_lookup = {t["song_id"]: t for t in album["tracks"]}
        album["tracks"] = [track_lookup[sid] for sid in new_order]
        album["song_ids"] = new_order

        self._albums[album_id] = album
        return album

