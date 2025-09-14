import importlib
import sqlite3
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "history.db"
    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as service_module
    importlib.reload(service_module)
    import backend.routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, service_module.schedule_service


def test_history_endpoint(tmp_path):
    client, svc = setup_app(tmp_path)

    act1 = svc.create_activity("Practice", 1.0, "music")
    act2 = svc.create_activity("Workout", 1.0, "fitness")

    svc.schedule_activity(1, "2024-01-01", 0, act1)
    svc.update_schedule_entry(1, "2024-01-01", 0, act2)
    svc.remove_schedule_entry(1, "2024-01-01", 0)

    resp = client.get("/schedule/history/2024-01-01")
    assert resp.status_code == 200
    data = resp.json()["history"]
    assert len(data) == 3
    assert data[0]["before"] is None and data[0]["after"]["activity_id"] == act1
    assert data[1]["before"]["activity_id"] == act1 and data[1]["after"]["activity_id"] == act2
    assert data[2]["before"]["activity_id"] == act2 and data[2]["after"] is None
