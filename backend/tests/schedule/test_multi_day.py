from pathlib import Path
from datetime import date, timedelta
import importlib
import pytest


def setup_db(tmp_path):
    db_file = tmp_path / "schedule.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as schedule_model
    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    import backend.services.schedule_service as service_module
    importlib.reload(service_module)
    return service_module.schedule_service


def test_multi_day_reservation(tmp_path):
    svc = setup_db(tmp_path)

    act_id = svc.create_activity("Tour", 1.0, "travel", duration_days=3)
    svc.schedule_activity(1, "2024-01-01", 8, act_id)

    for offset in range(3):
        day = (date.fromisoformat("2024-01-01") + timedelta(days=offset)).isoformat()
        sched = svc.get_daily_schedule(1, day)
        assert sched[0]["activity"]["id"] == act_id


def test_multi_day_conflict(tmp_path):
    svc = setup_db(tmp_path)

    long_id = svc.create_activity("Tour", 1.0, "travel", duration_days=2)
    svc.schedule_activity(1, "2024-01-01", 10, long_id)

    short_id = svc.create_activity("Practice", 1.0, "music")
    with pytest.raises(ValueError):
        svc.schedule_activity(1, "2024-01-02", 10, short_id)
