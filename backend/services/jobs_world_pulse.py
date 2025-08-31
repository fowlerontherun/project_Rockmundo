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
            genre = songs_genre.get(wid, "").strip() if wt == "song" else albums_genre.get(wid, "").strip()
            if not genre:
                continue
            totals[genre] = totals.get(genre, 0.0) + float(metric or 0.0) * CHART_SCORE_WEIGHT
        return totals

    def _media_signal_day(self, cur, date: str, bands_genre: Dict[int,str]) -> Dict[Tuple[str,str], float]:
        if not self._table_exists(cur, "media_effects"):
            return {}
        cur.execute("""
            SELECT band_id, region, value_int
            FROM media_effects
            WHERE effect_type = 'fame' AND date(created_at) = date(?)
        """, (date,))
        totals: Dict[Tuple[str,str], float] = {}
        for band_id, region, val in cur.fetchall():
            bid = int(band_id) if band_id is not None else None
            region = region or "Global"
            genre = bands_genre.get(bid, "").strip() if bid is not None else ""
            if not genre:
                continue
            key = (region, genre)
            totals[key] = totals.get(key, 0.0) + float(val or 0.0) * MEDIA_FAME_WEIGHT
        return totals

    # ---------- run daily ----------
    def run_daily(self, date: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            songs_genre, albums_genre, bands_genre = self._fetch_titles_genres(cur)

            streams = self._streams_signal_day(cur, date, songs_genre)
            charts  = self._charts_signal_day(cur, date, songs_genre, albums_genre)
            media   = self._media_signal_day(cur, date, bands_genre)

            global_scores: Dict[str, float] = {}
            for g, v in streams.items(): global_scores[g] = global_scores.get(g, 0.0) + v
            for g, v in charts.items():  global_scores[g] = global_scores.get(g, 0.0) + v

            region_scores: Dict[str, Dict[str, float]] = {}
            for (region, genre), val in media.items():
                region_scores.setdefault(region, {})
                region_scores[region][genre] = region_scores[region].get(genre, 0.0) + val

            cur.execute("BEGIN IMMEDIATE")
            cur.execute("DELETE FROM genre_pulse_snapshots WHERE period='daily' AND date=?", (date,))

            for genre, score in sorted(global_scores.items(), key=lambda x: (-x[1], x[0])):
                if not genre: continue
                sources = {"streams": streams.get(genre, 0.0), "charts": charts.get(genre, 0.0), "media": 0.0}
                cur.execute("""
                    INSERT INTO genre_pulse_snapshots (period, date, region, genre, score, sources_json)
                    VALUES ('daily', ?, 'Global', ?, ?, ?)
                """, (date, genre, float(score), json.dumps(sources)))

            for region, scores in region_scores.items():
                for genre, score in sorted(scores.items(), key=lambda x: (-x[1], x[0])):
                    if not genre: continue
                    sources = {"streams": 0.0, "charts": 0.0, "media": float(score)}
                    cur.execute("""
                        INSERT INTO genre_pulse_snapshots (period, date, region, genre, score, sources_json)
                        VALUES ('daily', ?, ?, ?, ?, ?)
                    """, (date, region, genre, float(score), json.dumps(sources)))
            conn.commit()
            return {"ok": True, "period": "daily", "date": date, "global_genres": len(global_scores), "regions": {r: len(vals) for r, vals in region_scores.items()}}

    # ---------- run weekly (Mon..Sun; date = Sunday) ----------
    def run_weekly(self, week_end_date: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()

            end_dt = datetime.strptime(week_end_date, "%Y-%m-%d")
            dates = [(end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

            region_genre_scores: Dict[Tuple[str,str], float] = {}
            for d in dates:
                cur.execute("""
                    SELECT region, genre, score
                    FROM genre_pulse_snapshots
                    WHERE period='daily' AND date = ?
                """, (d,))
                for region, genre, score in cur.fetchall():
                    key = (region, genre)
                    region_genre_scores[key] = region_genre_scores.get(key, 0.0) + float(score or 0.0)

            cur.execute("BEGIN IMMEDIATE")
            cur.execute("DELETE FROM genre_pulse_snapshots WHERE period='weekly' AND date=?", (week_end_date,))

            for (region, genre), score in sorted(region_genre_scores.items(), key=lambda x: (-x[1], x[0][1])):
                cur.execute("""
                    INSERT INTO genre_pulse_snapshots (period, date, region, genre, score, sources_json)
                    VALUES ('weekly', ?, ?, ?, ?, ?)
                """, (week_end_date, region, genre, float(score), json.dumps({"aggregated_days": dates})))
            conn.commit()
            by_region = {}
            for (region, _), _score in region_genre_scores.items():
                by_region[region] = by_region.get(region, 0) + 1
            return {"ok": True, "period": "weekly", "date": week_end_date, "regions": by_region}

    # ---------- queries ----------
    def top_genres(self, date: str, region: str = "Global", limit: int = 20, period: str = "daily") -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            cur.execute("""
                SELECT genre, score, sources_json
                FROM genre_pulse_snapshots
                WHERE period=? AND date=? AND region=?
                ORDER BY score DESC, genre ASC
                LIMIT ?
            """, (period, date, region, limit))
            rows = []
            for r in cur.fetchall():
                rows.append({"genre": r["genre"], "score": float(r["score"]), "sources": json.loads(r["sources_json"] or "{}")})
            return rows

    def trending(self, date: str, region: str = "Global", limit: int = 20, lookback: int = 7, period: str = "daily") -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()

            def map_for(d: str) -> Dict[str, float]:
                cur.execute("""
                    SELECT genre, score FROM genre_pulse_snapshots
                    WHERE period=? AND date=? AND region=?
                """, (period, d, region))
                return {r["genre"]: float(r["score"]) for r in cur.fetchall()}

            dt = datetime.strptime(date, "%Y-%m-%d")
            if period == "daily":
                prev = (dt - timedelta(days=lookback)).strftime("%Y-%m-%d")
            else:
                prev = (dt - timedelta(days=7 * lookback)).strftime("%Y-%m-%d")

            today_map = map_for(date)
            prev_map = map_for(prev)

            keys = set(today_map) | set(prev_map)
            deltas = []
            for g in keys:
                today = today_map.get(g, 0.0)
                prevv = prev_map.get(g, 0.0)
                delta = today - prevv
                if delta != 0.0:
                    deltas.append({"genre": g, "delta": float(delta), "today": float(today), "prev": float(prevv), "prev_date": prev})
            deltas.sort(key=lambda x: (-x["delta"], x["genre"]))
            return deltas[:limit]

    # ---------- UI helpers ----------
    def ui_ranked_list(self, date: str, region: str = "Global", limit: int = 20, period: str = "daily", lookback: int = None) -> List[Dict[str, Any]]:
        if lookback is None:
            lookback = 7 if period == "daily" else 1
        top = self.top_genres(date=date, region=region, limit=limit, period=period)
        delta_list = self.trending(date=date, region=region, limit=limit*2, lookback=lookback, period=period)
        delta_map = {d["genre"]: d for d in delta_list}
        out = []
        for idx, row in enumerate(top, start=1):
            g = row["genre"]; score = float(row["score"])
            d = delta_map.get(g)
            prev = float(d["prev"]) if d else score
            if prev == 0:
                delta_pct = 100.0 if score > 0 else 0.0
            else:
                delta_pct = ((score - prev) / abs(prev)) * 100.0
            emoji = "▲" if delta_pct > 5 else ("▼" if delta_pct < -5 else "→")
            out.append({
                "rank": idx,
                "genre": g,
                "score": round(score, 2),
                "delta_pct": round(delta_pct, 2),
                "trend_emoji": emoji
            })
        return out

    def ui_trending_movers(self, date: str, region: str = "Global", limit: int = 10, period: str = "daily", lookback: int = None) -> Dict[str, List[Dict[str, Any]]]:
        if lookback is None:
            lookback = 7 if period == "daily" else 1
        deltas = self.trending(date=date, region=region, limit=1000, lookback=lookback, period=period)
        gainers, losers = [], []
        for d in deltas:
            prev = d["prev"]
            delta = d["delta"]
            if prev == 0:
                delta_pct = 100.0 if d["today"] > 0 else 0.0
            else:
                delta_pct = (delta / abs(prev)) * 100.0
            row = {
                "genre": d["genre"],
                "delta": round(float(delta), 2),
                "delta_pct": round(float(delta_pct), 2),
                "trend_emoji": "▲" if delta > 0 else "▼",
                "today": round(float(d["today"]), 2),
                "prev": round(float(prev), 2),
                "prev_date": d["prev_date"]
            }
            if delta > 0: gainers.append(row)
            elif delta < 0: losers.append(row)
        gainers.sort(key=lambda x: (-x["delta_pct"], x["genre"]))
        losers.sort(key=lambda x: (x["delta_pct"], x["genre"]))
        for i, r in enumerate(gainers[:limit], start=1): r["rank"] = i
        for i, r in enumerate(losers[:limit], start=1): r["rank"] = i
        return {"gainers": gainers[:limit], "losers": losers[:limit]}

    def run_weekly_if_sunday(self, date: str) -> Optional[Dict[str, Any]]:
        if datetime.strptime(date, "%Y-%m-%d").weekday() == 6:
            return self.run_weekly(date)
        return None

    def run_all(self, date: str) -> Dict[str, Any]:
        # Apply daily decay to song popularity scores before computing pulses
        try:
            from backend.services.song_popularity_service import apply_decay

            apply_decay()
        except Exception:
            pass

        res = {"daily": self.run_daily(date)}
        wk = self.run_weekly_if_sunday(date)
        if wk: res["weekly"] = wk
        return res

    # ---------- sparkline ----------
    def sparkline_series(self, date: str, region: str = "Global", period: str = "daily", top_n: int = 5, points: int = 14) -> Dict[str, Any]:
        """
        Returns last N points for top_n genres at 'date' and 'region' for given period.
        For period='daily', points=days. For 'weekly', points=weeks (7-day jumps).
        Response:
        {
          "period":"daily",
          "region":"Global",
          "dates":["2025-08-01",...],
          "series":[{"genre":"Rock","values":[1.2,1.5,...]}, ...]
        }
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()

            # Find top genres on the target date
            cur.execute("""
                SELECT genre, score FROM genre_pulse_snapshots
                WHERE period=? AND date=? AND region=?
                ORDER BY score DESC, genre ASC
                LIMIT ?
            """, (period, date, region, top_n))
            top_genres = [r["genre"] for r in cur.fetchall()]
            if not top_genres:
                return {"period": period, "region": region, "dates": [], "series": []}

            # Build date list (ascending)
            end_dt = datetime.strptime(date, "%Y-%m-%d")
            step = timedelta(days=1 if period == "daily" else 7)
            dates = [(end_dt - i*step).strftime("%Y-%m-%d") for i in range(points-1, -1, -1)]

            # Fetch all rows for these dates/genres
            qmarks = ",".join(["?"]*len(dates))
            gmarks = ",".join(["?"]*len(top_genres))
            cur.execute(f"""
                SELECT date, genre, score
                FROM genre_pulse_snapshots
                WHERE period=? AND region=? AND date IN ({qmarks}) AND genre IN ({gmarks})
            """, (period, region, *dates, *top_genres))
            grid: Dict[Tuple[str,str], float] = {}
            for r in cur.fetchall():
                grid[(r["date"], r["genre"])] = float(r["score"])

            series = []
            for g in top_genres:
                values = [round(float(grid.get((d, g), 0.0)), 2) for d in dates]
                series.append({"genre": g, "values": values})

            return {"period": period, "region": region, "dates": dates, "series": series}
