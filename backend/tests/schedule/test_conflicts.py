import importlib
import sqlite3

import pytest


def setup_db(tmp_path):
    db_file = tmp_path / "conflicts.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as service_module

    importlib.reload(service_module)
    return service_module.schedule_service, db_file


def test_detects_conflicting_slots(tmp_path):
    svc, db_file = setup_db(tmp_path)

    act1 = svc.create_activity("Practice", 1.0, "music")
    act2 = svc.create_activity("Workout", 1.0, "fitness")

    svc.schedule_activity(1, "2024-01-01", 8, act1)

    with pytest.raises(ValueError) as exc:
        svc.schedule_activity(1, "2024-01-01", 10, act2)

    assert set(getattr(exc.value, "conflicts", [])) == {10, 11}


def test_auto_split_schedules_free_slots(tmp_path):
    svc, db_file = setup_db(tmp_path)

    long = svc.create_activity("Long", 1.0, "music")
    short = svc.create_activity("Short", 0.5, "music")

    svc.schedule_activity(1, "2024-01-01", 10, short)

    conflicts = svc.schedule_activity(
        1, "2024-01-01", 10, long, auto_split=True
    )

    assert set(conflicts) == {10, 11}

    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT slot FROM daily_schedule WHERE user_id=? AND date=? AND activity_id=?",
            (1, "2024-01-01", long),
        )
        slots = {row[0] for row in cur.fetchall()}

    assert slots == {12}

