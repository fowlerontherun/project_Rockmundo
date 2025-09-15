import importlib
import sqlite3
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "recurring.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as ds_model
    from backend.models import default_schedule as def_model
    from backend.models import daily_loop as dl_model
    from backend.models import recurring_schedule as rec_model

    activity_model.DB_PATH = db_file
    ds_model.DB_PATH = db_file
    def_model.DB_PATH = db_file
    dl_model.DB_PATH = db_file
    rec_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_service_module
    importlib.reload(schedule_service_module)
    import backend.services.scheduler_service as scheduler_service_module
    importlib.reload(scheduler_service_module)
    import routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_service_module.schedule_service, scheduler_service_module


def test_recurring_template_populates_daily_schedule(tmp_path):
    client, svc, scheduler_module = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 2, "music")
    weekday = date.today().strftime("%A").lower()
    svc.add_recurring_template(1, weekday, 9, act_id)

    # Ensure user exists in daily_loop with old login date
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO daily_loop (user_id, login_streak, last_login, current_challenge, challenge_progress, reward_claimed, catch_up_tokens, challenge_tier) VALUES (1,0,'2024-01-01','',0,0,0,1)"
        )
        conn.commit()

    scheduler_module.EVENT_HANDLERS["daily_loop_reset"]()
    today = date.today().isoformat()
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT activity_id FROM daily_schedule WHERE user_id=1 AND date=? AND hour=9",
            (today,),
        )
        row = cur.fetchone()
        assert row and row[0] == act_id


def test_inactive_template_not_applied(tmp_path):
    client, svc, scheduler_module = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 2, "music")
    weekday = date.today().strftime("%A").lower()
    template_id = svc.add_recurring_template(1, weekday, 10, act_id)
    svc.update_recurring_template(template_id, weekday, 10, act_id, active=False)

    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO daily_loop (user_id, login_streak, last_login, current_challenge, challenge_progress, reward_claimed, catch_up_tokens, challenge_tier) VALUES (1,0,'2024-01-01','',0,0,0,1)"
        )
        conn.commit()

    scheduler_module.EVENT_HANDLERS["daily_loop_reset"]()
    today = date.today().isoformat()
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM daily_schedule WHERE user_id=1 AND date=? AND hour=10",
            (today,),
        )
        count = cur.fetchone()[0]
        assert count == 0
