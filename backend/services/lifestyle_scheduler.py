# services/lifestyle_scheduler.py

import sqlite3
from datetime import datetime
from pathlib import Path
from types import ModuleType

from backend.config import lifestyle as lifestyle_config
from .xp_event_service import XPEventService

DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"


def lifestyle_xp_modifier(
    sleep: float,
    stress: float,
    discipline: float,
    mental: float,
    nutrition: float,
    fitness: float,
    thresholds: dict | None = None,
) -> float:
    """Return an XP modifier based on lifestyle metrics."""

    modifier = 1.0
    cfg = thresholds or lifestyle_config.MODIFIER_THRESHOLDS

    if sleep < cfg["sleep_hours"]["min"]:
        modifier *= cfg["sleep_hours"]["modifier"]
    if stress > cfg["stress"]["max"]:
        modifier *= cfg["stress"]["modifier"]
    if discipline < cfg["training_discipline"]["min"]:
        modifier *= cfg["training_discipline"]["modifier"]
    if mental < cfg["mental_health"]["min"]:
        modifier *= cfg["mental_health"]["modifier"]
    if nutrition < cfg["nutrition"]["min"]:
        modifier *= cfg["nutrition"]["modifier"]
    if fitness < cfg["fitness"]["min"]:
        modifier *= cfg["fitness"]["modifier"]

    return round(modifier, 2)

def apply_lifestyle_decay_and_xp_effects(
    config: ModuleType = lifestyle_config,
) -> int:
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
            stress = min(100, row[4] + config.DECAY["stress"])
            discipline = max(0, row[5] - config.DECAY["training_discipline"])
            mental = max(0, row[6] - config.DECAY["mental_health"])

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
            modifier = lifestyle_xp_modifier(
                sleep,
                stress,
                discipline,
                mental,
                nutrition,
                fitness,
                config.MODIFIER_THRESHOLDS,
            )
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
