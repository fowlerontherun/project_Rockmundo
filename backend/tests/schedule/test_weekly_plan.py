import importlib
import importlib
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "weekly.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import weekly_schedule as weekly_model

    activity_model.DB_PATH = db_file
    weekly_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_service_module
    importlib.reload(schedule_service_module)
    import backend.services.report_service as report_service_module
    importlib.reload(report_service_module)
    import backend.routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_service_module.schedule_service, report_service_module.report_service


def test_weekly_schedule_endpoints(tmp_path):
    client, svc, report = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 2, "music")

    resp = client.post(
        "/schedule/weekly/1/2024-01-01",
        json=[{"day": "mon", "slot": 9, "activity_id": act_id}],
    )
    assert resp.status_code == 200

    resp = client.get("/schedule/weekly/1/2024-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["schedule"][0]["activity"]["id"] == act_id

    # simulate completion in activity_log
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO activity_log(user_id, date, activity_id, outcome_json) VALUES (?,?,?,?)",
            (1, "2024-01-01", act_id, "{}"),
        )
        conn.commit()

    summary = report.weekly_summary(1, "2024-01-01")
    assert summary["scheduled_hours"] == 2
    assert summary["completed_hours"] == 2
