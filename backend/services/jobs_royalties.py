# File: backend/services/jobs_royalties.py
"""
Royalty Jobs Service
Aggregates revenue from streams + digital sales + vinyl into royalty_run_lines.
- Streams: sums per-song plays (anti-fraud cap per user/song/day) * per-stream rate
- Digital: sums digital_sales per work (song/album)
- Vinyl: sums per album via vinyl_order_items -> vinyl_skus(album_id)

If collaborations are present (table 'collaborations' with columns:
  work_type, work_id, band_a_id, band_b_id, split_a_pct, split_b_pct),
the amounts are split accordingly. Otherwise, full amount goes to the owner band
(if discoverable via songs.band_id or albums.band_id).

All tables are optional; if missing, that channel is skipped gracefully.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

STREAM_RATE_MICROCENTS = 30000  # 0.30 cents per stream = 30000 microcents
DAILY_STREAM_CAP_PER_USER_PER_SONG = 50  # anti-fraud cap

class RoyaltyJobError(Exception):
    pass

@dataclass
class RunWindow:
    start: str  # 'YYYY-MM-DD'
    end: str    # 'YYYY-MM-DD' (inclusive end handled in SQL <= end 23:59:59)

class RoyaltyJobsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- core helpers --------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS royalty_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              period_start TEXT NOT NULL,
              period_end TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              notes TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS royalty_run_lines (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              work_type TEXT NOT NULL,
              work_id INTEGER,
              band_id INTEGER,
              collaborator_band_id INTEGER,
              source TEXT NOT NULL,
              amount_cents INTEGER NOT NULL,
              meta_json TEXT,
              created_at TEXT DEFAULT (datetime('now'))
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_run ON royalty_run_lines(run_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_band ON royalty_run_lines(band_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_work ON royalty_run_lines(work_type, work_id)")
            conn.commit()

    def _create_run(self, cur, window: RunWindow) -> int:
        cur.execute("""
            INSERT INTO royalty_runs (period_start, period_end, status)
            VALUES (?, ?, 'running')
        """, (window.start, window.end))
        return cur.lastrowid

    def _complete_run(self, cur, run_id: int, notes: Optional[str] = None) -> None:
        cur.execute("""
            UPDATE royalty_runs SET status='completed', updated_at=datetime('now'), notes=COALESCE(notes, ?)
            WHERE id = ?
        """, (notes, run_id))

    def _fail_run(self, cur, run_id: int, err: str) -> None:
        cur.execute("""
            UPDATE royalty_runs SET status='failed', updated_at=datetime('now'), notes=?
            WHERE id = ?
        """, (err, run_id))

    # -------- ownership / collabs --------
    def _owner_band_for_work(self, cur, work_type: str, work_id: int) -> Optional[int]:
        try:
            if work_type == "song":
                cur.execute("SELECT band_id FROM songs WHERE id = ?", (work_id,))
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else None
            if work_type == "album":
                cur.execute("SELECT band_id FROM albums WHERE id = ?", (work_id,))
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else None
        except Exception:
            return None
        return None

    def _collab_split(self, cur, work_type: str, work_id: int) -> Optional[Tuple[int,int,int,int]]:
        """
        Returns (band_a_id, band_b_id, split_a_pct, split_b_pct) if a collab row exists.
        """
        try:
            cur.execute("""
                SELECT band_a_id, band_b_id, split_a_pct, split_b_pct
                FROM collaborations
                WHERE work_type = ? AND work_id = ?
            """, (work_type, work_id))
            row = cur.fetchone()
            if row:
                return int(row[0]), int(row[1]), int(row[2]), int(row[3])
        except Exception:
            return None
        return None

    def _emit_line(self, cur, run_id: int, work_type: str, work_id: Optional[int],
                   band_id: Optional[int], collaborator_band_id: Optional[int],
                   source: str, amount_cents: int, meta: Dict[str, Any]) -> None:
        cur.execute("""
            INSERT INTO royalty_run_lines (run_id, work_type, work_id, band_id, collaborator_band_id, source, amount_cents, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, work_type, work_id, band_id, collaborator_band_id, source, int(amount_cents), json.dumps(meta) if meta else None))

    # -------- channels --------
    def _process_streams(self, cur, run_id: int, window: RunWindow) -> None:
        if not self._table_exists(cur, "streams"):
            return
        # Aggregate plays per song with anti-fraud cap per user/day
        # Expect streams(created_at TEXT, song_id INTEGER, user_id INTEGER)
        cur.execute(f"""
            WITH capped AS (
              SELECT song_id, date(created_at) AS d, user_id, MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
              FROM streams
              WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?) 
              GROUP BY song_id, d, user_id
            ),
            sum_by_song AS (
              SELECT song_id, SUM(capped_plays) AS total_plays
              FROM capped
              GROUP BY song_id
            )
            SELECT song_id, total_plays FROM sum_by_song
        """, (f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        rows = cur.fetchall()
        for song_id, plays in rows:
            plays = int(plays or 0)
            microcents = plays * STREAM_RATE_MICROCENTS
            cents = microcents // 100  # convert microcents -> cents (floor)
            if cents <= 0:
                continue
            # Collab split?
            split = self._collab_split(cur, "song", song_id)
            if split:
                a_id, b_id, a_pct, b_pct = split
                a_amt = cents * a_pct // 100
                b_amt = cents - a_amt
                self._emit_line(cur, run_id, "song", song_id, a_id, b_id, "streams", a_amt, {"plays": plays, "split": f"{a_pct}/{b_pct}"})
                self._emit_line(cur, run_id, "song", song_id, b_id, a_id, "streams", b_amt, {"plays": plays, "split": f"{a_pct}/{b_pct}"})
            else:
                band_id = self._owner_band_for_work(cur, "song", song_id)
                self._emit_line(cur, run_id, "song", song_id, band_id, None, "streams", cents, {"plays": plays})

    def _process_digital(self, cur, run_id: int, window: RunWindow) -> None:
        if not self._table_exists(cur, "digital_sales"):
            return
        # Sum per work
        cur.execute("""
            SELECT work_type, work_id, SUM(price_cents) as revenue_cents, COUNT(*) as cnt
            FROM digital_sales
            WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
            GROUP BY work_type, work_id
        """, (f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        for work_type, work_id, revenue_cents, cnt in cur.fetchall():
            work_type = (work_type or "").lower()
            revenue_cents = int(revenue_cents or 0)
            if revenue_cents <= 0:
                continue
            if work_type not in ("song", "album"):
                work_type = "misc"
            split = self._collab_split(cur, work_type, int(work_id)) if work_type in ("song","album") else None
            meta = {"count": int(cnt)}
            if split and work_type in ("song","album"):
                a_id, b_id, a_pct, b_pct = split
                a_amt = revenue_cents * a_pct // 100
                b_amt = revenue_cents - a_amt
                self._emit_line(cur, run_id, work_type, int(work_id), a_id, b_id, "digital", a_amt, {**meta, "split": f"{a_pct}/{b_pct}"})
                self._emit_line(cur, run_id, work_type, int(work_id), b_id, a_id, "digital", b_amt, {**meta, "split": f"{a_pct}/{b_pct}"})
            else:
                band_id = self._owner_band_for_work(cur, work_type, int(work_id)) if work_type in ("song","album") else None
                self._emit_line(cur, run_id, work_type, int(work_id), band_id, None, "digital", revenue_cents, meta)

    def _process_vinyl(self, cur, run_id: int, window: RunWindow) -> None:
        # Requires vinyl_order_items, vinyl_orders, vinyl_skus (for album_id)
        needed = ["vinyl_order_items","vinyl_orders","vinyl_skus"]
        if not all(self._table_exists(cur, t) for t in needed):
            return
        cur.execute("""
            SELECT s.album_id, SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) AS revenue_cents,
                   SUM(oi.qty - oi.refunded_qty) as units
            FROM vinyl_order_items oi
            JOIN vinyl_orders o ON o.id = oi.order_id
            JOIN vinyl_skus s ON s.id = oi.sku_id
            WHERE o.status = 'confirmed'
              AND datetime(o.created_at) >= datetime(?)
              AND datetime(o.created_at) <= datetime(?)
            GROUP BY s.album_id
        """, (f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        for album_id, revenue_cents, units in cur.fetchall():
            revenue_cents = int(revenue_cents or 0)
            if revenue_cents <= 0:
                continue
            split = self._collab_split(cur, "album", int(album_id))
            meta = {"units": int(units)}
            if split:
                a_id, b_id, a_pct, b_pct = split
                a_amt = revenue_cents * a_pct // 100
                b_amt = revenue_cents - a_amt
                self._emit_line(cur, run_id, "album", int(album_id), a_id, b_id, "vinyl", a_amt, {**meta, "split": f"{a_pct}/{b_pct}"})
                self._emit_line(cur, run_id, "album", int(album_id), b_id, a_id, "vinyl", b_amt, {**meta, "split": f"{a_pct}/{b_pct}"})
            else:
                band_id = self._owner_band_for_work(cur, "album", int(album_id))
                self._emit_line(cur, run_id, "album", int(album_id), band_id, None, "vinyl", revenue_cents, meta)

    # -------- public API --------
    def run_royalties(self, period_start: str, period_end: str) -> Dict[str, Any]:
        """
        Execute a royalty run for [period_start, period_end] inclusive.
        Returns a summary with run_id and counts by channel.
        """
        window = RunWindow(period_start, period_end)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            try:
                cur.execute("BEGIN IMMEDIATE")
                run_id = self._create_run(cur, window)
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise

            # Process channels
            stats = {"streams": 0, "digital": 0, "vinyl": 0, "run_id": run_id}
            try:
                cur.execute("BEGIN IMMEDIATE")
                before = self._count_lines(cur, run_id)
                self._process_streams(cur, run_id, window)
                after = self._count_lines(cur, run_id); stats["streams"] = after - before

                before = self._count_lines(cur, run_id)
                self._process_digital(cur, run_id, window)
                after = self._count_lines(cur, run_id); stats["digital"] = after - before

                before = self._count_lines(cur, run_id)
                self._process_vinyl(cur, run_id, window)
                after = self._count_lines(cur, run_id); stats["vinyl"] = after - before

                self._complete_run(cur, run_id, notes=None)
                conn.commit()
            except Exception as e:
                conn.rollback()
                cur.execute("BEGIN IMMEDIATE")
                self._fail_run(cur, run_id, err=str(e))
                conn.commit()
                raise
            return stats

    def _count_lines(self, cur, run_id: int) -> int:
        cur.execute("SELECT COUNT(*) FROM royalty_run_lines WHERE run_id = ?", (run_id,))
        return int(cur.fetchone()[0])
