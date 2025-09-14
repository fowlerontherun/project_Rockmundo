import importlib


def setup_db(tmp_path):
    db_file = tmp_path / "schedule.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model
    from models import band_schedule as band_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    band_model.DB_PATH = db_file

    import backend.services.schedule_service as service_module
    importlib.reload(service_module)
    return service_module.schedule_service


def test_band_schedule_creation(tmp_path):
    svc = setup_db(tmp_path)

    act_id = svc.create_activity("Rehearsal", 1.0, "music")
    svc.schedule_band_activity(1, [10, 20], "2024-02-01", 16, act_id)

    band_sched = svc.get_band_schedule(1, "2024-02-01")
    assert band_sched == [
        {
            "slot": 16,
            "activity": {
                "id": act_id,
                "name": "Rehearsal",
                "duration_hours": 1.0,
                "category": "music",
            },
        }
    ]

    for uid in (10, 20):
        user_sched = svc.get_daily_schedule(uid, "2024-02-01")
        assert user_sched[0]["slot"] == 16
