# services/lifestyle_scheduler.py

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"

# Daily decay values
DECAY = {
    "sleep_hours": 0.2,
    "mental_health": 1.0,
    "stress": 1.5,
    "training_discipline": 0.5,
}

# XP modifier ranges
def lifestyle_xp_modifier(sleep, stress, discipline, mental):
    modifier = 1.0

    if sleep < 5: modifier *= 0.7
    if stress > 80: modifier *= 0.75
    if discipline < 30: modifier *= 0.85
    if mental < 60: modifier *= 0.8

    return round(modifier, 2)

def apply_lifestyle_decay_and_xp_effects():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM lifestyle")
        rows = cur.fetchall()

        for row in rows:
            user_id = row[1]
            sleep = max(0, row[2] - DECAY["sleep_hours"])
            drinking = row[3]
            stress = min(100, row[4] + DECAY["stress"])
            discipline = max(0, row[5] - DECAY["training_discipline"])
            mental = max(0, row[6] - DECAY["mental_health"])

            cur.execute("""
                UPDATE lifestyle
                SET sleep_hours = ?, stress = ?, training_discipline = ?, mental_health = ?, last_updated = ?
                WHERE user_id = ?
            """, (sleep, stress, discipline, mental, datetime.utcnow().isoformat(), user_id))

            modifier = lifestyle_xp_modifier(sleep, stress, discipline, mental)

            cur.execute("""
                INSERT INTO xp_modifiers (user_id, modifier, date)
                VALUES (?, ?, ?)
            """, (user_id, modifier, datetime.utcnow().date()))

        conn.commit()

# Optional: simulate daily task
if __name__ == "__main__":
    apply_lifestyle_decay_and_xp_effects()
    print("✅ Lifestyle decay + XP modifier applied.")
