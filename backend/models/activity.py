import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict

from backend.database import DB_PATH


@dataclass(frozen=True)
class Activity:
    name: str
    appearance_bonus: int


gym = Activity("gym", appearance_bonus=5)
running = Activity("running", appearance_bonus=3)
yoga = Activity("yoga", appearance_bonus=4)


def create_activity(
    name: str,
    duration_hours: float,
    category: str,
    required_skill: str | None = None,
    energy_cost: int = 0,
    rewards_json: str | None = None,
    duration_days: int = 1,
) -> int:
    """Insert a new activity and return its id."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO activities (name, duration_hours, duration_days, category, required_skill, energy_cost, rewards_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                duration_hours,
                duration_days,
                category,
                required_skill,
                energy_cost,
                rewards_json,
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_activity(activity_id: int) -> Optional[Dict]:
    """Retrieve an activity by id."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, duration_hours, duration_days, category, required_skill, energy_cost, rewards_json
            FROM activities WHERE id = ?
            """,
            (activity_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "duration_hours": row[2],
        "duration_days": row[3],
        "category": row[4],
        "required_skill": row[5],
        "energy_cost": row[6],
        "rewards_json": row[7],
    }


def list_activities() -> List[Dict]:
    """Return all activities."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, duration_hours, duration_days, category, required_skill, energy_cost, rewards_json
            FROM activities
            """
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "duration_hours": r[2],
            "duration_days": r[3],
            "category": r[4],
            "required_skill": r[5],
            "energy_cost": r[6],
            "rewards_json": r[7],
        }
        for r in rows
    ]


def update_activity(
    activity_id: int,
    name: str,
    duration_hours: float,
    category: str,
    required_skill: str | None = None,
    energy_cost: int = 0,
    rewards_json: str | None = None,
    duration_days: int = 1,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE activities
            SET name = ?, duration_hours = ?, duration_days = ?, category = ?, required_skill = ?, energy_cost = ?, rewards_json = ?
            WHERE id = ?
            """,
            (
                name,
                duration_hours,
                duration_days,
                category,
                required_skill,
                energy_cost,
                rewards_json,
                activity_id,
            ),
        )
        conn.commit()


def delete_activity(activity_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()


__all__ = [
    "Activity",
    "gym",
    "running",
    "yoga",
    "create_activity",
    "get_activity",
    "list_activities",
    "update_activity",
    "delete_activity",
]
