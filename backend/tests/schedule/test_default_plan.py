import importlib
import sqlite3
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "default.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as ds_model
    from backend.models import default_schedule as def_model
    from backend.models import daily_loop as dl_model

    activity_model.DB_PATH = db_file
    ds_model.DB_PATH = db_file
    def_model.DB_PATH = db_file
    dl_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_service_module
    importlib.reload(schedule_service_module)
    import backend.services.scheduler_service as scheduler_service_module
    importlib.reload(scheduler_service_module)
    import backend.routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_service_module.schedule_service, scheduler_service_module


def test_default_plan_endpoints(tmp_path):
    client, svc, _ = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 2, "music")
    today_name = date.today().strftime("%A").lower()
    resp = client.post(
        f"/schedule/default-plan/1/{today_name}",
        json=[{"hour": 9, "activity_id": act_id}],
    )
    assert resp.status_code == 200

    resp = client.get(f"/schedule/default-plan/1/{today_name}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"][0]["activity"]["id"] == act_id


def test_scheduler_populates_daily_schedule(tmp_path):
    client, svc, scheduler_module = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 2, "music")
    today_name = date.today().strftime("%A").lower()
    client.post(
        f"/schedule/default-plan/1/{today_name}",
        json=[{"hour": 9, "activity_id": act_id}],
    )

    # User has no login for today
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
