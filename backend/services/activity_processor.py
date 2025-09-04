"""Daily activity resolution service."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from typing import Dict, List

from backend.database import DB_PATH
from backend.models import activity_log as activity_log_model


def _ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_xp (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_energy (
            user_id INTEGER PRIMARY KEY,
            energy INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_skills (
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id, skill)
        )
        """,
    )


def _apply_effects(
    cur: sqlite3.Cursor, user_id: int, activity_id: int, slot: int
) -> Dict[str, int]:
    cur.execute(
        "SELECT duration_hours, rewards_json FROM activities WHERE id = ?",
        (activity_id,),
    )
    row = cur.fetchone()
    duration = row[0] if row else 1
    rewards = json.loads(row[1]) if row and row[1] else None
    if rewards:
        xp_gain = int(rewards.get("xp", 0))
        energy_change = int(rewards.get("energy", 0))
        skill_map = rewards.get("skills", {}) or {}
    else:
        xp_gain = int(duration * 10)
        energy_change = int(-duration * 5)
        skill_map = {}

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

    if skill_map:
        for skill, amount in skill_map.items():
            cur.execute(
                "INSERT OR IGNORE INTO user_skills(user_id, skill, level) VALUES (?, ?, 0)",
                (user_id, skill),
            )
            cur.execute(
                "UPDATE user_skills SET level = level + ? WHERE user_id = ? AND skill = ?",
                (amount, user_id, skill),
            )

    outcome: Dict[str, int] = {"xp": xp_gain, "energy": energy_change}
    if skill_map:
        outcome["skills"] = skill_map
    else:
        outcome["skill_gain"] = xp_gain
    # Commit so the activity log writer doesn't hit a lock
    cur.connection.commit()
    activity_log_model.record_outcome(
        user_id, _current_date, slot, activity_id, outcome
    )
    return outcome


# Helper variable used inside _apply_effects
_current_date: str


def process_day(target_date: str) -> Dict[str, int]:
    """Process all scheduled activities for ``target_date``."""
    global _current_date
    _current_date = target_date
    # Ensure activity log uses the same database
    activity_log_model.DB_PATH = DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_tables(cur)
        cur.execute(
            "SELECT user_id, slot, activity_id FROM daily_schedule WHERE date = ?",
            (target_date,),
        )
        rows: List[tuple[int, int, int]] = cur.fetchall()
        processed = 0
        for user_id, slot, activity_id in rows:
            _apply_effects(cur, user_id, activity_id, slot)
            processed += 1
        conn.commit()
    return {"status": "ok", "processed": processed}


def process_previous_day() -> Dict[str, int]:
    """Convenience wrapper to process yesterday's activities."""
    target_date = (date.today() - timedelta(days=1)).isoformat()
    return process_day(target_date)


def evaluate_schedule_completion(user_id: int, day: str) -> Dict[str, float]:
    """Return completion percentage for ``user_id`` on ``day`` and grant bonus."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM daily_schedule WHERE user_id=? AND date=?",
            (user_id, day),
        )
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM activity_log WHERE user_id=? AND date=?",
            (user_id, day),
        )
        completed = cur.fetchone()[0]
        completion = (completed / total * 100.0) if total else 0.0
        if total and completed == total:
            cur.execute(
                "INSERT OR IGNORE INTO user_xp(user_id, xp) VALUES (?, 0)",
                (user_id,),
            )
            cur.execute(
                "UPDATE user_xp SET xp = xp + 50 WHERE user_id=?",
                (user_id,),
            )
        conn.commit()
    return {"completion": round(completion, 2)}


__all__ = ["process_day", "process_previous_day", "evaluate_schedule_completion"]
