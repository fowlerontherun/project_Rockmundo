import importlib
import json
import sqlite3
from datetime import date, timedelta

import pytest


def setup_db(tmp_path):
    db_file = tmp_path / "activity.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    # ensure user_skills table for tests
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
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
        conn.commit()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_module
    importlib.reload(schedule_module)
    import backend.services.activity_processor as processor_module
    processor_module.DB_PATH = db_file
    importlib.reload(processor_module)

    return schedule_module.schedule_service, processor_module, db_file


def test_rejects_without_skill(tmp_path):
    schedule_svc, _, _ = setup_db(tmp_path)
    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    act_id = schedule_svc.create_activity(
        "Solo",
        1,
        "music",
        required_skill="guitar",
        energy_cost=0,
    )

    with pytest.raises(ValueError):
        schedule_svc.schedule_activity(user_id, yesterday, 10, act_id)


def test_rejects_on_low_energy(tmp_path):
    schedule_svc, _, db_file = setup_db(tmp_path)
    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_skills(user_id, skill, level) VALUES (?,?,?)",
            (user_id, "guitar", 1),
        )
        cur.execute(
            "INSERT INTO user_energy(user_id, energy) VALUES (?, ?)",
            (user_id, 5),
        )
        conn.commit()

    act_id = schedule_svc.create_activity(
        "Jam",
        1,
        "music",
        required_skill="guitar",
        energy_cost=10,
    )

    with pytest.raises(ValueError):
        schedule_svc.schedule_activity(user_id, yesterday, 9, act_id)


def test_rewards_applied(tmp_path):
    schedule_svc, processor, db_file = setup_db(tmp_path)
    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_skills(user_id, skill, level) VALUES (?,?,?)",
            (user_id, "guitar", 1),
        )
        conn.commit()

    rewards = {"xp": 40, "energy": 5, "skills": {"guitar": 3}}
    act_id = schedule_svc.create_activity(
        "Practice Solo",
        1,
        "music",
        required_skill="guitar",
        energy_cost=10,
        rewards_json=json.dumps(rewards),
    )

    schedule_svc.schedule_activity(user_id, yesterday, 8, act_id)
    processor.process_previous_day()

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT xp FROM user_xp WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == rewards["xp"]
        cur.execute("SELECT energy FROM user_energy WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 95  # 100 - 10 + 5
        cur.execute(
            "SELECT level FROM user_skills WHERE user_id = ? AND skill = ?",
            (user_id, "guitar"),
        )
        assert cur.fetchone()[0] == 4
        cur.execute(
            "SELECT outcome_json FROM activity_log WHERE user_id = ? AND date = ?",
            (user_id, yesterday),
        )
        outcome = json.loads(cur.fetchone()[0])
        assert outcome == {"xp": 40, "energy": 5, "skills": {"guitar": 3}}
