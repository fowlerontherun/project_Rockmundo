# File: backend/services/jobs_world_pulse.py
"""
World Pulse / Trending Genres Dashboard service with:
- Daily + Weekly snapshots
- UI lists (ranked, trending movers)
- Sparkline time-series for top genres
- Admin "run-all" helper
"""
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

STREAMS_PLAY_WEIGHT = 0.01
CHART_SCORE_WEIGHT = 1.0
MEDIA_FAME_WEIGHT = 0.5
DAILY_STREAM_CAP_PER_USER_PER_SONG = 50

class WorldPulseError(Exception):
    pass

@dataclass
class Window:
    date: str  # YYYY-MM-DD

class WorldPulseService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # ---------- schema ----------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS genre_pulse_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              period TEXT NOT NULL,
              date TEXT NOT NULL,
              region TEXT NOT NULL,
              genre TEXT NOT NULL,
              score REAL NOT NULL,
              sources_json TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              UNIQUE(period, date, region, genre)
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_pulse_date_region ON genre_pulse_snapshots(date, region)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_pulse_genre ON genre_pulse_snapshots(genre)")
            conn.commit()

    # ---------- helpers ----------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def _fetch_titles_genres(self, cur) -> Tuple[Dict[int,str], Dict[int,str], Dict[int,str]]:
        songs_genre, albums_genre, bands_genre = {}, {}, {}
        try:
            cur.execute("SELECT id, COALESCE(genre, '') FROM songs")
            songs_genre = {int(r[0]): (r[1] or '').strip() for r in cur.fetchall() if r[1] is not None}
        except Exception:
            pass
        try:
            cur.execute("SELECT id, COALESCE(genre, '') FROM albums")
            albums_genre = {int(r[0]): (r[1] or '').strip() for r in cur.fetchall() if r[1] is not None}
        except Exception:
            pass
        try:
            cur.execute("SELECT id, COALESCE(primary_genre, '') FROM bands")
            bands_genre = {int(r[0]): (r[1] or '').strip() for r in cur.fetchall() if r[1] is not None}
        except Exception:
            pass
        return songs_genre, albums_genre, bands_genre

    # ---------- signals (single-day) ----------
    def _streams_signal_day(self, cur, date: str, songs_genre: Dict[int,str]) -> Dict[str, float]:
        if not self._table_exists(cur, "streams"):
            return {}
        cur.execute(f"""
            WITH capped AS (
              SELECT song_id, date(created_at) AS d, user_id, MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
              FROM streams
              WHERE date(created_at) = date(?)
              GROUP BY song_id, d, user_id
            ),
            tot AS (
              SELECT song_id, SUM(capped_plays) AS plays FROM capped GROUP BY song_id
            )
            SELECT song_id, plays FROM tot
        """, (date,))
        genre_totals: Dict[str, int] = {}
        for song_id, plays in cur.fetchall():
            gid = int(song_id)
            plays = int(plays or 0)
            genre = songs_genre.get(gid, "").strip()
            if not genre:
                continue
            genre_totals[genre] = genre_totals.get(genre, 0) + plays
        return {g: v * STREAMS_PLAY_WEIGHT for g, v in genre_totals.items()}

    def _charts_signal_day(self, cur, date: str, songs_genre: Dict[int,str], albums_genre: Dict[int,str]) -> Dict[str, float]:
        if not self._table_exists(cur, "chart_snapshots"):
            return {}
        cur.execute("""
            SELECT work_type, work_id, metric_value
            FROM chart_snapshots
            WHERE chart_type = 'combined_song' AND period = 'daily' AND period_start = ?
        """, (date,))
        totals: Dict[str, float] = {}
        for work_type, work_id, metric in cur.fetchall():
            wt = (work_type or "").lower()
            wid = int(work_id)
            genre = songs_genre.get(wid, "

