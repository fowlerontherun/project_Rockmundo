import importlib
import json
import sqlite3
from datetime import date, timedelta


def setup_db(tmp_path):
    db_file = tmp_path / "activity.db"
    from backend import database

    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_module
    importlib.reload(schedule_module)

    import backend.services.activity_processor as processor_module
    processor_module.DB_PATH = db_file
    importlib.reload(processor_module)

    return schedule_module.schedule_service, processor_module


def test_activity_processing_persists_outcomes(tmp_path):
    schedule_svc, processor = setup_db(tmp_path)

    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    act_id = schedule_svc.create_activity("Practice", 2, "music")
    schedule_svc.schedule_activity(user_id, yesterday, 9, act_id)

    result = processor.process_previous_day()
    assert result["processed"] == 1

    with sqlite3.connect(processor.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT xp FROM user_xp WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 20
        cur.execute("SELECT energy FROM user_energy WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 90
        cur.execute(
            "SELECT outcome_json FROM activity_log WHERE user_id = ? AND date = ?",
            (user_id, yesterday),
        )
        outcome = json.loads(cur.fetchone()[0])
        assert outcome == {"xp": 20, "energy": -10, "skill_gain": 20}
