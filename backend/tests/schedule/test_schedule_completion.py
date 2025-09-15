import importlib
import sqlite3
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "sched.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import activity_log as log_model
    from backend.models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file
    log_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_module
    importlib.reload(schedule_module)

    import backend.services.activity_processor as processor_module
    processor_module.DB_PATH = db_file
    importlib.reload(processor_module)

    import routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_module.schedule_service, processor_module, log_model


def test_schedule_completion_and_bonus(tmp_path):
    client, svc, processor, log_model = setup_app(tmp_path)
    uid = 1
    day = date.today().isoformat()

    act1 = svc.create_activity("Practice", 1, "music")
    act2 = svc.create_activity("Workout", 1, "health")
    svc.schedule_activity(uid, day, 0, act1)
    svc.schedule_activity(uid, day, 4, act2)

    log_model.record_outcome(uid, day, 0, act1, {"xp": 10})
    stats = processor.evaluate_schedule_completion(uid, day)
    assert stats["completion"] == 50.0
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT xp FROM user_xp WHERE user_id=?", (uid,))
        assert cur.fetchone() is None

    log_model.record_outcome(uid, day, 4, act2, {"xp": 10})
    resp = client.get(f"/schedule/stats/{uid}/{day}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion"] == 100.0
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT xp FROM user_xp WHERE user_id=?", (uid,))
        assert cur.fetchone()[0] == 50
