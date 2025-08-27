"""Service for managing band rehearsal sessions.

This module provides minimal scheduling with conflict detection and
practice bonuses that feed back into a band's skill progression and
upcoming performance quality.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class RehearsalService:
    """Simple SQLite backed rehearsal scheduler."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self._ensure_schema()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        return conn

    def _ensure_schema(self) -> None:
        """Create required tables if they do not yet exist."""

        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS bands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    skill REAL DEFAULT 0,
                    performance_quality REAL DEFAULT 0
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS rehearsals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    band_id INTEGER NOT NULL,
                    start TEXT NOT NULL,
                    end TEXT NOT NULL,
                    attendees TEXT,
                    bonus REAL DEFAULT 0,
                    FOREIGN KEY(band_id) REFERENCES bands(id)
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS rehearsal_attendance (
                    rehearsal_id INTEGER,
                    member_id INTEGER,
                    UNIQUE(rehearsal_id, member_id)
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def book_session(
        self, band_id: int, start: str, end: str, attendees: Iterable[int]
    ) -> dict:
        """Book a rehearsal session.

        Raises:
            ValueError: if the booking conflicts with an existing session.
        """

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if end_dt <= start_dt:
            raise ValueError("End must be after start")

        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT start, end FROM rehearsals WHERE band_id = ?",
                (band_id,),
            )
            for row in c.fetchall():
                exist_start = datetime.fromisoformat(row[0])
                exist_end = datetime.fromisoformat(row[1])
                if not (end_dt <= exist_start or start_dt >= exist_end):
                    raise ValueError("Booking conflict")

            attendee_list: List[int] = list(attendees)
            bonus = float(len(attendee_list)) * 0.5
            c.execute(
                """
                INSERT INTO rehearsals(band_id, start, end, attendees, bonus)
                VALUES (?,?,?,?,?)
                """,
                (
                    band_id,
                    start_dt.isoformat(),
                    end_dt.isoformat(),
                    ",".join(str(a) for a in attendee_list),
                    bonus,
                ),
            )
            rehearsal_id = c.lastrowid
            # update band skills and performance
            c.execute(
                "UPDATE bands SET skill = skill + ?, performance_quality = performance_quality + ? WHERE id = ?",
                (bonus, bonus * 0.5, band_id),
            )
            conn.commit()
        return {"rehearsal_id": rehearsal_id, "bonus": bonus}

    def record_attendance(self, rehearsal_id: int, member_id: int) -> None:
        """Mark a band member as present for a rehearsal."""

        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO rehearsal_attendance(rehearsal_id, member_id) VALUES (?, ?)",
                (rehearsal_id, member_id),
            )
            conn.commit()

    def attendance(self, rehearsal_id: int) -> List[int]:
        """Return a list of member ids that attended a rehearsal."""

        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT member_id FROM rehearsal_attendance WHERE rehearsal_id = ?",
                (rehearsal_id,),
            )
            return [row[0] for row in c.fetchall()]


__all__ = ["RehearsalService"]

