import json
import sqlite3
from typing import Dict, List

from models.album import Album

from backend.database import DB_PATH


class LiveAlbumService:
    """Compile live albums from existing performance recordings."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or str(DB_PATH)

    # ------------------------------------------------------------------
    def _has_performance_score(self, cur: sqlite3.Cursor) -> bool:
        cur.execute("PRAGMA table_info(live_performances)")
        return any(row[1] == "performance_score" for row in cur.fetchall())

    # ------------------------------------------------------------------
    def compile_live_album(self, performance_ids: List[int], title: str) -> Dict:
        if len(performance_ids) != 5:
            raise ValueError("Exactly five performance IDs are required")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        has_score = self._has_performance_score(cur)

        performances = []
        for pid in performance_ids:
            if has_score:
                cur.execute(
                    "SELECT rowid, band_id, setlist, skill_gain, performance_score FROM live_performances WHERE rowid = ?",
                    (pid,),
                )
            else:
                cur.execute(
                    "SELECT rowid, band_id, setlist, skill_gain FROM live_performances WHERE rowid = ?",
                    (pid,),
                )
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError(f"Performance {pid} not found")
            if has_score:
                rowid, band_id, setlist_json, skill_gain, perf_score = row
            else:
                rowid, band_id, setlist_json, skill_gain = row
                perf_score = None
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
            performances.append(
                {
                    "id": rowid,
                    "band_id": band_id,
                    "songs": songs,
                    "metric": perf_score if perf_score is not None else skill_gain,
                    "order": songs,
                }
            )
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
        tracks = []
        for song_id in order:
            best = max(
                (p for p in performances if song_id in p["songs"]),
                key=lambda p: p["metric"],
            )
            tracks.append({"song_id": song_id, "performance_id": best["id"]})
        album = Album(
            id=0,
            title=title,
            album_type="live",
            genre_id=0,
            band_id=performances[0]["band_id"],
            song_ids=[t["song_id"] for t in tracks],
        )
        data = album.to_dict()
        data["tracks"] = tracks
        return data
