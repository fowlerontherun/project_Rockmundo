# services/schedule_service.py

"""Daily schedule management helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Mapping

DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"


def _ensure_table(cur: sqlite3.Cursor) -> None:
    """Ensure the schedule table exists."""

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            tag TEXT NOT NULL,
            hours REAL NOT NULL
        )
        """
    )


def save_daily_plan(
    user_id: int, day: str, activities: Iterable[Mapping[str, float]]
) -> dict:
    """Persist a daily plan after validating required rest.

    Each activity in ``activities`` must provide ``tag`` and ``hours`` keys. The
    total ``hours`` of activities tagged ``rest`` or ``sleep`` must be at least
    five; otherwise a ``ValueError`` is raised.
    """

    rest_hours = sum(
        act.get("hours", 0)
        for act in activities
        if act.get("tag") in {"rest", "sleep"}
    )
    if rest_hours < 5:
        raise ValueError("Daily plan must include ≥5 hours of rest/sleep")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
        # Replace any existing plan for this user/day
        cur.execute(
            "DELETE FROM schedule WHERE user_id = ? AND day = ?",
            (user_id, day),
        )
        for act in activities:
            cur.execute(
                "INSERT INTO schedule (user_id, day, tag, hours) VALUES (?, ?, ?, ?)",
                (user_id, day, act["tag"], act["hours"]),
            )
        conn.commit()

    return {"status": "ok"}


__all__ = ["save_daily_plan"]

