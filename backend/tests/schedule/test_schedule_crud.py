import importlib
from pathlib import Path


def setup_db(tmp_path):
    db_file = tmp_path / "schedule.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    # reload models to pick up patched DB_PATH
    from backend.models import activity as activity_model
    from backend.models import daily_schedule as schedule_model
    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    import backend.services.schedule_service as service_module
    importlib.reload(service_module)
    return service_module.schedule_service


def test_create_and_retrieve_schedule(tmp_path):
    svc = setup_db(tmp_path)

    act_id = svc.create_activity("Practice", 1.5, "music")
    svc.schedule_activity(1, "2024-01-01", 38, act_id)  # 09:30 slot

    schedule = svc.get_daily_schedule(1, "2024-01-01")
    assert schedule == [
        {
            "slot": 38,
            "activity": {
                "id": act_id,
                "name": "Practice",
                "duration_hours": 1.5,
                "category": "music",
            },
        }
    ]


def test_update_schedule_entry(tmp_path):
    svc = setup_db(tmp_path)

    act1 = svc.create_activity("Practice", 2.0, "music")
    act2 = svc.create_activity("Workout", 0.5, "fitness")

    svc.schedule_activity(1, "2024-01-01", 36, act1)
    svc.update_schedule_entry(1, "2024-01-01", 36, act2)

    schedule = svc.get_daily_schedule(1, "2024-01-01")
    assert schedule[0]["slot"] == 36
    assert schedule[0]["activity"]["id"] == act2
