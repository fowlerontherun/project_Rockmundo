import sqlite3
from typing import Dict, List

from backend.database import DB_PATH

# Maximum number of exercise activities permitted in a single day.
# Additional exercise sessions beyond this limit are rejected when
# attempting to add or update entries.
MAX_EXERCISE_ACTIVITIES_PER_DAY = 1


def _check_exercise_limit(cur: sqlite3.Cursor, user_id: int, date: str, activity_id: int) -> None:
    """Ensure the user has not exceeded their daily exercise allowance.

    Parameters
    ----------
    cur:
        Open database cursor.
    user_id:
        The id of the user being scheduled.
    date:
        The schedule date in ISO format.
    activity_id:
        The id of the activity being scheduled.

    Raises
    ------
    ValueError
        If scheduling the activity would exceed the allowed number of
        exercise sessions for the specified day.
    """

    cur.execute("SELECT category FROM activities WHERE id = ?", (activity_id,))
    row = cur.fetchone()
    if not row or row[0] != "exercise":
        return

    cur.execute(
        """
        SELECT COUNT(*)
        FROM daily_schedule ds
        JOIN activities a ON ds.activity_id = a.id
        WHERE ds.user_id = ? AND ds.date = ? AND a.category = 'exercise'
        """,
        (user_id, date),
    )
    count = cur.fetchone()[0]
    if count >= MAX_EXERCISE_ACTIVITIES_PER_DAY:
        raise ValueError("daily exercise activity limit reached")


def add_entry(user_id: int, date: str, slot: int, activity_id: int) -> None:
    """Insert or update a schedule entry for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _check_exercise_limit(cur, user_id, date, activity_id)
        cur.execute(
            """
            INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date, slot) DO UPDATE SET activity_id = excluded.activity_id, hour = excluded.hour
            """,
            (user_id, date, slot, slot, activity_id),
        )
        conn.commit()


def update_entry(user_id: int, date: str, slot: int, activity_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _check_exercise_limit(cur, user_id, date, activity_id)
        cur.execute(
            "UPDATE daily_schedule SET activity_id = ?, hour = ? WHERE user_id = ? AND date = ? AND slot = ?",
            (activity_id, slot, user_id, date, slot),
        )
        conn.commit()


def remove_entry(user_id: int, date: str, slot: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM daily_schedule WHERE user_id = ? AND date = ? AND slot = ?",
            (user_id, date, slot),
        )
        conn.commit()


def clear_day(user_id: int, date: str) -> None:
    """Remove all schedule entries for a user on a given day."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM daily_schedule WHERE user_id = ? AND date = ?",
            (user_id, date),
        )
        conn.commit()


def find_conflicts(
    user_id: int, date: str, start_slot: int, duration_slots: int
) -> List[int]:
    """Return occupied slots within the proposed activity window.

    Because only the starting slot of each scheduled activity is stored,
    this helper derives the occupied range for each entry using the
    activity's duration.
    """

    end_slot = start_slot + duration_slots
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ds.slot, a.duration_hours
            FROM daily_schedule ds
            JOIN activities a ON ds.activity_id = a.id
            WHERE ds.user_id = ? AND ds.date = ?
            """,
            (user_id, date),
        )
        rows = cur.fetchall()

    conflicts: set[int] = set()
    requested = range(start_slot, end_slot)
    for slot, duration in rows:
        span = range(slot, slot + int(duration * 4))
        conflicts.update(s for s in span if s in requested)

    return sorted(conflicts)


def get_schedule(user_id: int, date: str) -> List[Dict]:
    """Return all scheduled activities for a user on a given date."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ds.slot, a.id, a.name, a.duration_hours, a.category
            FROM daily_schedule ds
            JOIN activities a ON ds.activity_id = a.id
            WHERE ds.user_id = ? AND ds.date = ?
            ORDER BY ds.slot
            """,
            (user_id, date),
        )
        rows = cur.fetchall()
    return [
        {
            "slot": r[0],
            "activity": {
                "id": r[1],
                "name": r[2],
                "duration_hours": r[3],
                "category": r[4],
            },
        }
        for r in rows
    ]


__all__ = [
    "add_entry",
    "update_entry",
    "remove_entry",
    "clear_day",
    "find_conflicts",
    "get_schedule",
]
