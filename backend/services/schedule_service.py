
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


from typing import List, Dict

from backend.models import activity as activity_model
from backend.models import daily_schedule as schedule_model
from backend.models import default_schedule as default_model


class ScheduleService:
    """Service layer wrapping activity and daily schedule operations."""

    # Activity CRUD -----------------------------------------------------
    def create_activity(self, name: str, duration_hours: int, category: str) -> int:
        return activity_model.create_activity(name, duration_hours, category)

    def get_activity(self, activity_id: int) -> Dict | None:
        return activity_model.get_activity(activity_id)

    def update_activity(
        self, activity_id: int, name: str, duration_hours: int, category: str
    ) -> None:
        activity_model.update_activity(activity_id, name, duration_hours, category)

    def delete_activity(self, activity_id: int) -> None:
        activity_model.delete_activity(activity_id)

    # Schedule logic ----------------------------------------------------
    def schedule_activity(
        self, user_id: int, date: str, hour: int, activity_id: int
    ) -> None:
        schedule_model.add_entry(user_id, date, hour, activity_id)

    def update_schedule_entry(
        self, user_id: int, date: str, hour: int, activity_id: int
    ) -> None:
        schedule_model.update_entry(user_id, date, hour, activity_id)

    def remove_schedule_entry(self, user_id: int, date: str, hour: int) -> None:
        schedule_model.remove_entry(user_id, date, hour)

    def get_daily_schedule(self, user_id: int, date: str) -> List[Dict]:
        return schedule_model.get_schedule(user_id, date)

    # Default plan logic ----------------------------------------------
    def set_default_plan(self, user_id: int, day_of_week: str, plan: List[Dict]) -> None:
        entries = ((p["hour"], p["activity_id"]) for p in plan)
        default_model.set_plan(user_id, day_of_week, entries)

    def get_default_plan(self, user_id: int, day_of_week: str) -> List[Dict]:
        return default_model.get_plan(user_id, day_of_week)


schedule_service = ScheduleService()

__all__ = ["ScheduleService", "schedule_service"]

