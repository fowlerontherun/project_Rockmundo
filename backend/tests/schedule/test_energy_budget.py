from datetime import date, datetime, timedelta

import importlib
import sqlite3

import pytest


def setup_db(tmp_path):
    db_file = tmp_path / "energy.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    # Point models at the temp database
    from models import activity as activity_model
    from models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_module
    importlib.reload(schedule_module)
    import backend.services.lifestyle_scheduler as lifestyle_module
    importlib.reload(lifestyle_module)
    lifestyle_module.DB_PATH = db_file

    return schedule_module.schedule_service, lifestyle_module, db_file


def test_day_limit_enforced(tmp_path):
    schedule_svc, _, _ = setup_db(tmp_path)

    user_id = 1
    day = (date.today() - timedelta(days=1)).isoformat()

    long_act = schedule_svc.create_activity("Long Jam", 20, "music")
    schedule_svc.schedule_activity(user_id, day, 0, long_act)

    extra_act = schedule_svc.create_activity("Overload", 5, "music")
    with pytest.raises(ValueError):
        schedule_svc.schedule_activity(user_id, day, 80, extra_act)


def test_energy_recovery(tmp_path):
    _, lifestyle_module, db_file = setup_db(tmp_path)

    today = datetime.utcnow().date().isoformat()

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        # Minimal user and lifestyle setup
        cur.execute(
            "INSERT INTO users(username, password_hash) VALUES(?, ?)",
            ("alice", "pw"),
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO lifestyle(user_id) VALUES (?)", (user_id,))
        cur.execute("INSERT INTO user_energy(user_id, energy) VALUES (?, ?)", (user_id, 50))
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS xp_modifiers (
                user_id INTEGER,
                modifier REAL NOT NULL,
                date TEXT NOT NULL
            )
            """
        )
        # Record sleep hours for today so energy can recover
        cur.execute(
            "INSERT INTO schedule(user_id, day, tag, hours) VALUES (?,?,?,?)",
            (user_id, today, "sleep", 5),
        )
        conn.commit()

    lifestyle_module.apply_lifestyle_decay_and_xp_effects()

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT energy FROM user_energy WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 100  # 50 + 5*10 capped at 100

