import math
import math
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from backend.database import DB_PATH
from backend.services.song_popularity_forecast import forecast_service

# Supported region codes and platforms
ALLOWED_REGION_CODES = {"global", "US", "EU"}
SUPPORTED_PLATFORMS = {"any", "spotify", "apple"}


def _validate_region_platform(region_code: str, platform: str) -> None:
    """Ensure region code and platform are supported."""
    if region_code not in ALLOWED_REGION_CODES:
        raise ValueError(f"Invalid region_code: {region_code}")
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Invalid platform: {platform}")

# Popularity decay factors by legacy state
DECAY_FACTOR = 0.95  # for new songs
CLASSIC_DECAY_FACTOR = 0.98
RETIRED_ROYALTY_EVENT = 1  # minimal residual royalty payout

# Derived half-life in days for the default decay factor
HALF_LIFE_DAYS = math.log(0.5) / math.log(DECAY_FACTOR)


def _ensure_schema(cur: sqlite3.Cursor) -> None:
    """Ensure required tables exist."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_popularity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            region_code TEXT NOT NULL DEFAULT 'global',
            platform TEXT NOT NULL DEFAULT 'any',
            popularity_score REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    # Indexes to speed up common queries on song popularity
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_song_id ON song_popularity(song_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_region_code ON song_popularity(region_code)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_platform ON song_popularity(platform)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_updated_at ON song_popularity(updated_at)"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_popularity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            region_code TEXT NOT NULL DEFAULT 'global',
            platform TEXT NOT NULL DEFAULT 'any',
            source TEXT NOT NULL,
            boost INTEGER NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Indexes to speed up queries on popularity events
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_events_song_id ON song_popularity_events(song_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_events_region_code ON song_popularity_events(region_code)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_events_platform ON song_popularity_events(platform)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_popularity_events_created_at ON song_popularity_events(created_at)"
    )


class SongPopularityService:
    """Track song popularity boosts from various media events."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH

    def add_event(
        self,
        song_id: int,
        source: str,
        boost: int,
        region_code: str = "global",
        platform: str = "any",
        details: str = "",
    ) -> Dict[str, int]:
        """Apply a popularity boost and log the event."""
        _validate_region_platform(region_code, platform)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            now = datetime.utcnow().isoformat()
            cur.execute(
                """
                INSERT INTO song_popularity_events
                    (song_id, region_code, platform, source, boost, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (song_id, region_code, platform, source, boost, details, now),
            )
            cur.execute(
                """
                SELECT popularity_score FROM song_popularity
                WHERE song_id=? AND region_code=? AND platform=?
                ORDER BY updated_at DESC LIMIT 1
                """,
                (song_id, region_code, platform),
            )
            row = cur.fetchone()
            current = float(row[0]) if row else 0.0
            new_score = current + float(boost)
            cur.execute(
                """
                INSERT INTO song_popularity
                    (song_id, region_code, platform, popularity_score, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (song_id, region_code, platform, new_score, now),
            )
            conn.commit()
            # Recompute forecasts whenever a popularity event occurs
            try:
                forecast_service.forecast_song(song_id)
            except Exception:
                pass
            return {
                "song_id": song_id,
                "region_code": region_code,
                "platform": platform,
                "score": int(new_score),
            }

    def list_events(
        self,
        song_id: Optional[int] = None,
        region_code: Optional[str] = None,
        platform: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            query = (
                "SELECT id, song_id, region_code, platform, source, boost, details, created_at FROM song_popularity_events"
            )
            params: List = []
            conditions = []
            if song_id is not None:
                conditions.append("song_id = ?")
                params.append(song_id)
            if region_code is not None:
                conditions.append("region_code = ?")
                params.append(region_code)
            if platform is not None:
                conditions.append("platform = ?")
                params.append(platform)
            if source is not None:
                conditions.append("source = ?")
                params.append(source)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "song_id": r[1],
                    "region_code": r[2],
                    "platform": r[3],
                    "source": r[4],
                    "boost": r[5],
                    "details": r[6],
                    "created_at": r[7],
                }
                for r in rows
            ]


# Singleton used across the app
song_popularity_service = SongPopularityService()


def add_event(
    song_id: int,
    amount: float,
    source: str,
    region_code: str = "global",
    platform: str = "any",
    details: str = "",
) -> float:
    """Boost a song's popularity by a given amount from some source."""
    _validate_region_platform(region_code, platform)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            """
            SELECT popularity_score FROM song_popularity
            WHERE song_id=? AND region_code=? AND platform=?
            ORDER BY updated_at DESC LIMIT 1
            """,
            (song_id, region_code, platform),
        )
        row = cur.fetchone()
        current = float(row[0]) if row else 0.0
        new_score = current + float(amount)
        now = datetime.utcnow().isoformat()
        cur.execute(
            """
            INSERT INTO song_popularity
                (song_id, region_code, platform, popularity_score, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (song_id, region_code, platform, new_score, now),
        )
        cur.execute(
            """
            INSERT INTO song_popularity_events
                (song_id, region_code, platform, source, boost, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (song_id, region_code, platform, source, amount, details, now),
        )
        conn.commit()
        try:
            forecast_service.forecast_song(song_id)
        except Exception:
            pass
        return new_score


def apply_decay() -> int:
    """Apply decay based on song legacy state."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        try:
            cur.execute(
                """
                SELECT sp.song_id, sp.region_code, sp.platform, sp.popularity_score, s.legacy_state
                FROM song_popularity sp
                LEFT JOIN songs s ON s.id = sp.song_id
                WHERE (sp.song_id, sp.region_code, sp.platform, sp.updated_at) IN (
                    SELECT song_id, region_code, platform, MAX(updated_at)
                    FROM song_popularity GROUP BY song_id, region_code, platform
                )
                """
            )
        except sqlite3.OperationalError:
            cur.execute(
                """
                SELECT song_id, region_code, platform, popularity_score, NULL
                FROM song_popularity
                WHERE (song_id, region_code, platform, updated_at) IN (
                    SELECT song_id, region_code, platform, MAX(updated_at)
                    FROM song_popularity GROUP BY song_id, region_code, platform
                )
                """
            )
        rows = cur.fetchall()
        now = datetime.utcnow().isoformat()
        decayed = []
        for song_id, region_code, platform, score, legacy in rows:
            state = legacy or "new"
            if state == "retired":
                cur.execute(
                    """
                    INSERT INTO song_popularity_events
                        (song_id, region_code, platform, source, boost, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        song_id,
                        region_code,
                        platform,
                        "retired_royalty",
                        RETIRED_ROYALTY_EVENT,
                        "minimal residual royalties",
                        now,
                    ),
                )
                continue
            factor = CLASSIC_DECAY_FACTOR if state == "classic" else DECAY_FACTOR
            decayed.append((song_id, region_code, platform, score * factor, now))
        if decayed:
            cur.executemany(
                """
                INSERT INTO song_popularity
                    (song_id, region_code, platform, popularity_score, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                decayed,
            )
        conn.commit()
        return len(decayed)


def get_history(
    song_id: int,
    region_code: str = "global",
    platform: str = "any",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, float]]:
    """Return the popularity history for a song."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        _ensure_schema(cur)
        query = (
            "SELECT popularity_score, updated_at FROM song_popularity "
            "WHERE song_id=? AND region_code=? AND platform=?"
        )
        params: List = [song_id, region_code, platform]
        if start_date:
            query += " AND updated_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND updated_at <= ?"
            params.append(end_date)
        query += " ORDER BY updated_at"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def get_current_popularity(
    song_id: int,
    region_code: str = "global",
    platform: str = "any",
) -> float:
    """Return the latest popularity score for a song."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            """
            SELECT popularity_score FROM song_popularity
            WHERE song_id=? AND region_code=? AND platform=?
            ORDER BY updated_at DESC LIMIT 1
            """,
            (song_id, region_code, platform),
        )
        row = cur.fetchone()
        return float(row[0]) if row else 0.0


def get_last_boost_source(
    song_id: int,
    region_code: str = "global",
    platform: str = "any",
) -> Optional[str]:
    """Return the source of the most recent popularity boost."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            """
            SELECT source FROM song_popularity_events
            WHERE song_id=? AND region_code=? AND platform=?
            ORDER BY id DESC LIMIT 1
            """,
            (song_id, region_code, platform),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_breakdown(
    song_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Dict[str, float]]:
    """Return latest popularity scores grouped by region and platform."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        _ensure_schema(cur)
        query = (
            "SELECT region_code, platform, popularity_score, updated_at FROM song_popularity "
            "WHERE song_id=?"
        )
        params: List = [song_id]
        if start_date:
            query += " AND updated_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND updated_at <= ?"
            params.append(end_date)
        query += " ORDER BY updated_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
    breakdown: Dict[str, Dict[str, float]] = {}
    seen = set()
    for r in rows:
        key = (r["region_code"], r["platform"])
        if key in seen:
            continue
        seen.add(key)
        breakdown.setdefault(r["region_code"], {})[r["platform"]] = r["popularity_score"]
    return breakdown


def aggregate_global_popularity() -> int:
    """Aggregate regional popularity into global totals."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            """
            SELECT song_id, region_code, platform, popularity_score FROM song_popularity
            WHERE (song_id, region_code, platform, updated_at) IN (
                SELECT song_id, region_code, platform, MAX(updated_at)
                FROM song_popularity GROUP BY song_id, region_code, platform
            )
            """
        )
        rows = cur.fetchall()
        totals: Dict[int, float] = {}
        for song_id, region_code, platform, score in rows:
            if region_code == "global" and platform == "any":
                continue
            totals[song_id] = totals.get(song_id, 0.0) + float(score)
        now = datetime.utcnow().isoformat()
        inserts = [
            (sid, "global", "any", total, now) for sid, total in totals.items()
        ]
        if inserts:
            cur.executemany(
                """
                INSERT INTO song_popularity
                    (song_id, region_code, platform, popularity_score, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                inserts,
            )
        conn.commit()
        return len(inserts)


def schedule_global_aggregation() -> None:
    """Schedule daily aggregation of regional popularity into global totals."""
    try:
        from datetime import timedelta

        from backend.services.scheduler_service import schedule_task

        run_at = (datetime.utcnow() + timedelta(days=1)).isoformat()
        schedule_task(
            "aggregate_global_popularity",
            {},
            run_at,
            recurring=True,
            interval_days=1,
        )
    except Exception:
        # Scheduling is best effort; ignore failures if scheduler tables don't exist
        pass


# Attempt to schedule aggregation on import
schedule_global_aggregation()

