# services/lifestyle_scheduler.py

import sqlite3
from datetime import datetime
from pathlib import Path

from .xp_event_service import XPEventService

DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"

# Daily decay values (sleep is derived from schedule and not decayed)
DECAY = {
    "mental_health": 1.0,
    "stress": 1.5,
    "training_discipline": 0.5,
}

# XP modifier ranges
def lifestyle_xp_modifier(sleep, stress, discipline, mental):
    modifier = 1.0

    if sleep < 5:
        modifier *= 0.7
    if stress > 80:
        modifier *= 0.75
    if discipline < 30:
        modifier *= 0.85
    if mental < 60:
        modifier *= 0.8

    return round(modifier, 2)

def apply_lifestyle_decay_and_xp_effects():
    from .skill_service import skill_service  # local import to avoid cycle

    event_svc = XPEventService()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM lifestyle")
        rows = cur.fetchall()

        today = datetime.utcnow().date().isoformat()
        # Ensure schedule table exists for lookups
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

        for row in rows:
            user_id = row[1]

            # Sum hours tagged as rest or sleep for today
            cur.execute(
                """
                SELECT COALESCE(SUM(hours), 0)
                FROM schedule
                WHERE user_id = ? AND day = ? AND tag IN ('rest', 'sleep')
                """,
                (user_id, today),
            )
            sleep = cur.fetchone()[0]

            _drinking = row[3]
            stress = min(100, row[4] + DECAY["stress"])
            discipline = max(0, row[5] - DECAY["training_discipline"])
            mental = max(0, row[6] - DECAY["mental_health"])

            cur.execute(
                """
                UPDATE lifestyle
                SET sleep_hours = ?, stress = ?, training_discipline = ?, mental_health = ?, last_updated = ?
                WHERE user_id = ?
                """,
                (
                    sleep,
                    stress,
                    discipline,
                    mental,
                    datetime.utcnow().isoformat(),
                    user_id,
                ),
            )

            modifier = lifestyle_xp_modifier(sleep, stress, discipline, mental)
            modifier *= event_svc.get_active_multiplier()

            cur.execute("""
                INSERT INTO xp_modifiers (user_id, modifier, date)
                VALUES (?, ?, ?)
            """, (user_id, modifier, datetime.utcnow().date()))

            # Daily lifestyle decay affects skills slightly
            skill_service.apply_daily_decay(user_id)

        conn.commit()

# Optional: simulate daily task
if __name__ == "__main__":
    apply_lifestyle_decay_and_xp_effects()
    print("✅ Lifestyle decay + XP modifier applied.")
