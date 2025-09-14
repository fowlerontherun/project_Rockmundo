import importlib
from pathlib import Path


def setup_db(tmp_path):
    db_file = tmp_path / "schedule.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model
    from models import user_settings as settings_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    settings_model.DB_PATH = db_file

    import backend.services.schedule_service as service_module
    importlib.reload(service_module)

    return service_module.schedule_service, schedule_model, settings_model


def test_timezone_conversion(tmp_path):
    svc, schedule_model, settings_model = setup_db(tmp_path)

    act = svc.create_activity("Practice", 1.0, "music")

    settings_model.set_settings(1, "light", "", [], "US/Pacific")
    svc.schedule_activity(1, "2024-01-01", 32, act)
    entries = schedule_model.get_schedule(1, "2024-01-01")
    assert entries[0]["slot"] == 64
    sched = svc.get_daily_schedule(1, "2024-01-01")
    assert sched[0]["slot"] == 32

    settings_model.set_settings(2, "light", "", [], "Asia/Tokyo")
    svc.schedule_activity(2, "2024-01-02", 2, act)
    entries2 = schedule_model.get_schedule(2, "2024-01-01")
    assert entries2[0]["slot"] == 62
    sched2 = svc.get_daily_schedule(2, "2024-01-02")
    assert sched2[0]["slot"] == 2
