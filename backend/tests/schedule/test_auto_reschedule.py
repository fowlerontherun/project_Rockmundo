import importlib
import sqlite3
from datetime import date, timedelta


def setup_db(tmp_path):
    db_file = tmp_path / "activity.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model
    from models import next_day_schedule as next_model
    from models import user_settings as settings_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    next_model.DB_PATH = db_file
    settings_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_module
    importlib.reload(schedule_module)

    import backend.services.activity_processor as processor_module
    processor_module.DB_PATH = db_file
    importlib.reload(processor_module)

    return schedule_module.schedule_service, processor_module, settings_model


def test_uncompleted_tasks_rescheduled(tmp_path):
    schedule_svc, processor, settings_model = setup_db(tmp_path)

    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()

    act_id = schedule_svc.create_activity("Practice", 2, "music")
    schedule_svc.schedule_activity(user_id, yesterday, 9, act_id)

    settings_model.set_settings(user_id, "light", "", [], "UTC", True)

    result = processor.process_previous_day()
    assert result["processed"] == 0

    with sqlite3.connect(processor.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT activity_id FROM next_day_schedule WHERE user_id=? AND date=?",
            (user_id, today),
        )
        row = cur.fetchone()
        assert row is not None and row[0] == act_id

    schedule = schedule_svc.get_daily_schedule(user_id, today)
    assert schedule[0]["activity"]["id"] == act_id
    assert schedule[0]["rescheduled"] is True
