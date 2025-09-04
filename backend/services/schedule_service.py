
# services/schedule_service.py

"""Daily schedule management helpers."""

from __future__ import annotations

import sqlite3
import json
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


from typing import List, Dict, Iterable

from backend.models import activity as activity_model
from backend.models import band_schedule as band_schedule_model
from backend.models import daily_schedule as schedule_model
from backend.models import default_schedule as default_model
from backend.models import weekly_schedule as weekly_model
from backend.models import recurring_schedule as recurring_model


def _log_schedule_change(user_id: int, date: str, slot: int, before, after) -> None:
    """Persist an audit record for schedule mutations."""
    with sqlite3.connect(schedule_model.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO schedule_audit (user_id, date, slot, before_state, after_state)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                date,
                slot,
                json.dumps(before) if before is not None else None,
                json.dumps(after) if after is not None else None,
            ),
        )
        conn.commit()


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

            # Ensure the user does not exceed 24 hours of scheduled time
            cur.execute(
                """
                SELECT COALESCE(SUM(a.duration_hours), 0)
                FROM daily_schedule ds
                JOIN activities a ON ds.activity_id = a.id
                WHERE ds.user_id = ? AND ds.date = ?
                """,
                (user_id, date),
            )
            day_hours = cur.fetchone()[0]
            if day_hours + duration_hours > 24:
                raise ValueError("Day exceeds 24 hours")
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

        with sqlite3.connect(schedule_model.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT activity_id FROM daily_schedule WHERE user_id=? AND date=? AND slot=?",
                (user_id, date, slot),
            )
            row = cur.fetchone()
            before = {"activity_id": row[0]} if row else None

        schedule_model.add_entry(user_id, date, slot, activity_id)
        _log_schedule_change(
            user_id, date, slot, before, {"activity_id": activity_id}
        )
        return original_conflicts if auto_split else None

    def update_schedule_entry(
        self, user_id: int, date: str, slot: int, activity_id: int
    ) -> None:
        with sqlite3.connect(schedule_model.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT activity_id FROM daily_schedule WHERE user_id=? AND date=? AND slot=?",
                (user_id, date, slot),
            )
            row = cur.fetchone()
            before = {"activity_id": row[0]} if row else None

        schedule_model.update_entry(user_id, date, slot, activity_id)
        _log_schedule_change(
            user_id, date, slot, before, {"activity_id": activity_id}
        )

    def remove_schedule_entry(self, user_id: int, date: str, slot: int) -> None:
        with sqlite3.connect(schedule_model.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT activity_id FROM daily_schedule WHERE user_id=? AND date=? AND slot=?",
                (user_id, date, slot),
            )
            row = cur.fetchone()
            before = {"activity_id": row[0]} if row else None

        schedule_model.remove_entry(user_id, date, slot)
        _log_schedule_change(user_id, date, slot, before, None)

    def get_daily_schedule(self, user_id: int, date: str) -> List[Dict]:
        return schedule_model.get_schedule(user_id, date)

    def get_schedule_history(self, date: str) -> List[Dict]:
        with sqlite3.connect(schedule_model.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, slot, before_state, after_state, changed_at FROM schedule_audit WHERE date=? ORDER BY id",
                (date,),
            )
            rows = cur.fetchall()
        history: List[Dict] = []
        for uid, slot, before, after, ts in rows:
            history.append(
                {
                    "user_id": uid,
                    "slot": slot,
                    "before": json.loads(before) if before else None,
                    "after": json.loads(after) if after else None,
                    "changed_at": ts,
                }
            )
        return history

    # Band schedule logic --------------------------------------------
    def schedule_band_activity(
        self,
        band_id: int,
        member_ids: Iterable[int],
        date: str,
        slot: int,
        activity_id: int,
    ) -> None:
        for uid in member_ids:
            schedule_model.add_entry(uid, date, slot, activity_id)
        band_schedule_model.add_entry(band_id, date, slot, activity_id)

    def get_band_schedule(self, band_id: int, date: str) -> List[Dict]:
        return band_schedule_model.get_schedule(band_id, date)

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

    # Recurring templates ---------------------------------------------
    def add_recurring_template(
        self, user_id: int, pattern: str, hour: int, activity_id: int, active: bool = True
    ) -> int:
        return recurring_model.add_template(user_id, pattern, hour, activity_id, active)

    def update_recurring_template(
        self,
        template_id: int,
        pattern: str,
        hour: int,
        activity_id: int,
        active: bool = True,
    ) -> None:
        recurring_model.update_template(
            template_id, pattern, hour, activity_id, active
        )

    def remove_recurring_template(self, template_id: int) -> None:
        recurring_model.remove_template(template_id)

    def get_recurring_templates(self, user_id: int) -> List[Dict]:
        return recurring_model.get_templates(user_id)

    # Default plan logic ----------------------------------------------
    def set_default_plan(self, user_id: int, day_of_week: str, plan: List[Dict]) -> None:
        entries = ((p["hour"], p["activity_id"]) for p in plan)
        default_model.set_plan(user_id, day_of_week, entries)

    def get_default_plan(self, user_id: int, day_of_week: str) -> List[Dict]:
        return default_model.get_plan(user_id, day_of_week)


schedule_service = ScheduleService()

__all__ = ["ScheduleService", "schedule_service"]

