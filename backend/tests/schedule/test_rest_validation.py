import sqlite3

import pytest

from backend.services import schedule_service


def _init_db(path):
    schedule_service.DB_PATH = path
    # touch the database file and ensure a clean schedule table
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS schedule")
        conn.commit()


def test_rejects_when_rest_under_five(tmp_path):
    db = tmp_path / "sched.db"
    _init_db(db)

    plan = [
        {"tag": "practice", "hours": 10},
        {"tag": "sleep", "hours": 4},
    ]

    with pytest.raises(ValueError):
        schedule_service.save_daily_plan(1, "2024-01-01", plan)


def test_accepts_valid_rest(tmp_path):
    db = tmp_path / "sched.db"
    _init_db(db)

    plan = [
        {"tag": "practice", "hours": 8},
        {"tag": "sleep", "hours": 5},
    ]

    result = schedule_service.save_daily_plan(1, "2024-01-01", plan)
    assert result["status"] == "ok"

    with sqlite3.connect(schedule_service.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT SUM(hours) FROM schedule WHERE user_id=1 AND tag IN ('sleep','rest')"
        )
        assert cur.fetchone()[0] == 5

