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
def lifestyle_xp_modifier(sleep, stress, discipline, mental, nutrition, fitness):
    modifier = 1.0

    if sleep < 5:
        modifier *= 0.7
    if stress > 80:
        modifier *= 0.75
    if discipline < 30:
        modifier *= 0.85
    if mental < 60:
        modifier *= 0.8
    if nutrition < 40:
        modifier *= 0.9
    if fitness < 30:
        modifier *= 0.9

    return round(modifier, 2)

def apply_lifestyle_decay_and_xp_effects() -> int:
    from .skill_service import skill_service  # local import to avoid cycle
    from .lifestyle_service import grant_daily_xp, log_exercise_session
    from .addiction_service import addiction_service
    try:
        from .random_event_service import random_event_service
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        random_event_service = None

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
        # Ensure user_energy table exists for recovery
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_energy (
                user_id INTEGER PRIMARY KEY,
                energy INTEGER NOT NULL DEFAULT 100
            )
            """
        )

        count = 0
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

            # Process scheduled exercise and apply cooldown-based benefits
            cur.execute(
                """
                SELECT tag, SUM(hours)
                FROM schedule
                WHERE user_id = ? AND day = ? AND tag IN ('exercise', 'gym', 'running', 'yoga')
                GROUP BY tag
                """,
                (user_id, today),
            )
            exercise_rows = cur.fetchall()
            for tag, hours in exercise_rows:
                if hours <= 0:
                    continue
                # default to 'gym' if legacy tag used
                activity = tag if tag in ('gym', 'running', 'yoga') else 'gym'
                log_exercise_session(user_id, int(hours * 60), activity, conn)

            # Additional penalties from addictions
            addiction_level = addiction_service.get_highest_level(user_id)
            if addiction_level > 0:
                mental = max(0, mental - addiction_level * 0.1)

                missed = addiction_service.check_for_missed_events(user_id, today)
                if missed:
                    from backend.models.daily_schedule import remove_entry

                    for entry in missed:
                        remove_entry(user_id, today, entry["slot"])
                    random_event_service.trigger_addiction_event(
                        user_id, level=addiction_level, date=today
                    )

                if addiction_level >= 50 and random_event_service:
                    random_event_service.trigger_addiction_event(user_id)

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

            # Recover energy based on sleep, capped at 100
            cur.execute(
                "INSERT OR IGNORE INTO user_energy(user_id, energy) VALUES (?, 100)",
                (user_id,),
            )
            cur.execute(
                "SELECT energy FROM user_energy WHERE user_id = ?",
                (user_id,),
            )
            current_energy = cur.fetchone()[0]
            recovered = int(sleep * 10)
            new_energy = min(100, current_energy + recovered)
            cur.execute(
                "UPDATE user_energy SET energy = ? WHERE user_id = ?",
                (new_energy, user_id),
            )

            nutrition = row[7]
            fitness = row[8]
            modifier = lifestyle_xp_modifier(sleep, stress, discipline, mental, nutrition, fitness)
            modifier *= event_svc.get_active_multiplier()

            cur.execute("""
                INSERT INTO xp_modifiers (user_id, modifier, date)
                VALUES (?, ?, ?)
            """, (user_id, modifier, datetime.utcnow().date()))

            data = {
                "sleep_hours": sleep,
                "stress": stress,
                "training_discipline": discipline,
                "mental_health": mental,
                "nutrition": nutrition,
                "fitness": fitness,
            }
            grant_daily_xp(user_id, data, conn)

            conn.commit()

            # Daily lifestyle decay affects skills slightly
            skill_service.apply_daily_decay(user_id)

            count += 1

        return count

# Optional: simulate daily task
if __name__ == "__main__":
    apply_lifestyle_decay_and_xp_effects()
    print("✅ Lifestyle decay + XP modifier applied.")
