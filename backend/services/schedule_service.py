
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
from backend.models import weekly_schedule as weekly_model


class ScheduleService:
    """Service layer wrapping activity and daily schedule operations."""

    # Activity CRUD -----------------------------------------------------
    def create_activity(
        self,
        name: str,
        duration_hours: float,
        category: str,
        required_skill: str | None = None,
        energy_cost: int = 0,
        rewards_json: str | None = None,
    ) -> int:
        return activity_model.create_activity(
            name, duration_hours, category, required_skill, energy_cost, rewards_json
        )

    def get_activity(self, activity_id: int) -> Dict | None:
        return activity_model.get_activity(activity_id)

    def update_activity(
        self,
        activity_id: int,
        name: str,
        duration_hours: float,
        category: str,
        required_skill: str | None = None,
        energy_cost: int = 0,
        rewards_json: str | None = None,
    ) -> None:
        activity_model.update_activity(
            activity_id,
            name,
            duration_hours,
            category,
            required_skill,
            energy_cost,
            rewards_json,
        )

    def delete_activity(self, activity_id: int) -> None:
        activity_model.delete_activity(activity_id)

    # Schedule logic ----------------------------------------------------
    def schedule_activity(
        self,
        user_id: int,
        date: str,
        slot: int,
        activity_id: int,
        auto_split: bool = False,
    ) -> List[int] | None:
        """Schedule an activity after validating requirements and energy.

        If ``auto_split`` is ``False`` and the requested activity conflicts with
        existing entries, a ``ValueError`` is raised with a ``conflicts``
        attribute listing the occupied slots. When ``auto_split`` is ``True``,
        the activity is shifted forward until a free window of the required
        duration is found and the originally conflicting slots are returned.
        """

        with sqlite3.connect(schedule_model.DB_PATH) as conn:
            cur = conn.cursor()
            # Ensure helper tables
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_skills (
                    user_id INTEGER NOT NULL,
                    skill TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(user_id, skill)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_energy (
                    user_id INTEGER PRIMARY KEY,
                    energy INTEGER NOT NULL DEFAULT 100
                )
                """
            )
            cur.execute(
                "SELECT required_skill, energy_cost, duration_hours FROM activities WHERE id = ?",
                (activity_id,),
            )
            row = cur.fetchone()
            req_skill = row[0] if row else None
            energy_cost = row[1] if row else 0
            duration_hours = row[2] if row else 0
            if req_skill:
                cur.execute(
                    "SELECT level FROM user_skills WHERE user_id = ? AND skill = ?",
                    (user_id, req_skill),
                )
                skill_row = cur.fetchone()
                if not skill_row or skill_row[0] <= 0:
                    raise ValueError("User lacks required skill")
            cur.execute(
                "INSERT OR IGNORE INTO user_energy(user_id, energy) VALUES (?, 100)",
                (user_id,),
            )
            cur.execute(
                "SELECT energy FROM user_energy WHERE user_id = ?",
                (user_id,),
            )
            energy = cur.fetchone()[0]
            if energy < energy_cost:
                raise ValueError("Insufficient energy")
            if energy_cost:
                cur.execute(
                    "UPDATE user_energy SET energy = energy - ? WHERE user_id = ?",
                    (energy_cost, user_id),
                )
            conn.commit()

        slots_needed = max(1, int(duration_hours * 4))
        conflicts = schedule_model.find_conflicts(user_id, date, slot, slots_needed)
        original_conflicts = list(conflicts)
        if conflicts:
            if auto_split:
                # shift start until a free window is found
                new_slot = slot
                while conflicts:
                    new_slot = max(conflicts) + 1
                    conflicts = schedule_model.find_conflicts(
                        user_id, date, new_slot, slots_needed
                    )
                slot = new_slot
            else:
                err = ValueError("Schedule conflict")
                err.conflicts = conflicts
                raise err

        schedule_model.add_entry(user_id, date, slot, activity_id)
        return original_conflicts if auto_split else None

    def update_schedule_entry(
        self, user_id: int, date: str, slot: int, activity_id: int
    ) -> None:
        schedule_model.update_entry(user_id, date, slot, activity_id)

    def remove_schedule_entry(self, user_id: int, date: str, slot: int) -> None:
        schedule_model.remove_entry(user_id, date, slot)

    def get_daily_schedule(self, user_id: int, date: str) -> List[Dict]:
        return schedule_model.get_schedule(user_id, date)

    # Weekly schedule logic -------------------------------------------
    def set_weekly_schedule(self, user_id: int, week_start: str, plan: List[Dict]) -> None:
        entries = ((p["day"], p["slot"], p["activity_id"]) for p in plan)
        weekly_model.set_schedule(user_id, week_start, entries)

    def get_weekly_schedule(self, user_id: int, week_start: str) -> List[Dict]:
        return weekly_model.get_schedule(user_id, week_start)

    def add_weekly_entry(
        self, user_id: int, week_start: str, day: str, slot: int, activity_id: int
    ) -> None:
        weekly_model.add_entry(user_id, week_start, day, slot, activity_id)

    def update_weekly_entry(
        self, user_id: int, week_start: str, day: str, slot: int, activity_id: int
    ) -> None:
        weekly_model.update_entry(user_id, week_start, day, slot, activity_id)

    def remove_weekly_entry(
        self, user_id: int, week_start: str, day: str, slot: int
    ) -> None:
        weekly_model.remove_entry(user_id, week_start, day, slot)

    # Default plan logic ----------------------------------------------
    def set_default_plan(self, user_id: int, day_of_week: str, plan: List[Dict]) -> None:
        entries = ((p["hour"], p["activity_id"]) for p in plan)
        default_model.set_plan(user_id, day_of_week, entries)

    def get_default_plan(self, user_id: int, day_of_week: str) -> List[Dict]:
        return default_model.get_plan(user_id, day_of_week)


schedule_service = ScheduleService()

__all__ = ["ScheduleService", "schedule_service"]

