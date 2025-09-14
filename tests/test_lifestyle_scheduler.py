import sqlite3
from datetime import datetime

from services import lifestyle_scheduler, xp_reward_service


def test_scheduler_applies_xp_without_lock(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(lifestyle_scheduler, "DB_PATH", db_path)
    monkeypatch.setattr(xp_reward_service.xp_reward_service, "db_path", str(db_path))

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE lifestyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_hours REAL,
            drinking TEXT,
            stress REAL,
            training_discipline REAL,
            mental_health REAL,
            nutrition REAL,
            fitness REAL,
            last_updated TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE xp_modifiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            modifier REAL NOT NULL,
            date TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE user_levels (
            user_id INTEGER PRIMARY KEY,
            level INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated) VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 10, 50, 70, 50, 50, datetime.utcnow().isoformat()),
    )
    cur.execute("INSERT INTO user_levels (user_id, level) VALUES (?, ?)", (1, 1))
    conn.commit()
    conn.close()

    # Should not raise "database is locked" and should award XP
    assert lifestyle_scheduler.apply_lifestyle_decay_and_xp_effects() == 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT amount FROM hidden_xp_rewards WHERE user_id = ?", (1,))
    assert cur.fetchone() is not None
    conn.close()

