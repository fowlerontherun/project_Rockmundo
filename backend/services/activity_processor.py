"""Daily activity resolution service."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from typing import Dict, List

from backend.database import DB_PATH


def _ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_xp (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_energy (
            user_id INTEGER PRIMARY KEY,
            energy INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            activity_id INTEGER NOT NULL,
            outcome_json TEXT NOT NULL
        )
        """
    )


def _apply_effects(cur: sqlite3.Cursor, user_id: int, activity_id: int) -> Dict[str, int]:
    cur.execute(
        "SELECT duration_hours FROM activities WHERE id = ?",
        (activity_id,),
    )
    row = cur.fetchone()
    duration = row[0] if row else 1
    xp_gain = int(duration * 10)
    energy_change = int(-duration * 5)
    skill_gain = xp_gain  # simplified

    cur.execute(
        "INSERT OR IGNORE INTO user_xp(user_id, xp) VALUES (?, 0)",
        (user_id,),
    )
    cur.execute(
        "UPDATE user_xp SET xp = xp + ? WHERE user_id = ?",
        (xp_gain, user_id),
    )
    cur.execute(
        "INSERT OR IGNORE INTO user_energy(user_id, energy) VALUES (?, 100)",
        (user_id,),
    )
    cur.execute(
        "UPDATE user_energy SET energy = energy + ? WHERE user_id = ?",
        (energy_change, user_id),
    )

    outcome = {"xp": xp_gain, "energy": energy_change, "skill_gain": skill_gain}
    cur.execute(
        "INSERT INTO activity_log(user_id, date, activity_id, outcome_json) VALUES (?, ?, ?, ?)",
        (user_id, _current_date, activity_id, json.dumps(outcome)),
    )
    return outcome


# Helper variable used inside _apply_effects
_current_date: str


def process_day(target_date: str) -> Dict[str, int]:
    """Process all scheduled activities for ``target_date``."""
    global _current_date
    _current_date = target_date
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_tables(cur)
        cur.execute(
            "SELECT user_id, activity_id FROM daily_schedule WHERE date = ?",
            (target_date,),
        )
        rows: List[tuple[int, int]] = cur.fetchall()
        processed = 0
        for user_id, activity_id in rows:
            _apply_effects(cur, user_id, activity_id)
            processed += 1
        conn.commit()
    return {"status": "ok", "processed": processed}


def process_previous_day() -> Dict[str, int]:
    """Convenience wrapper to process yesterday's activities."""
    target_date = (date.today() - timedelta(days=1)).isoformat()
    return process_day(target_date)


__all__ = ["process_day", "process_previous_day"]
