import importlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "calendar.db"
    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as service_module
    importlib.reload(service_module)
    import backend.services.calendar_export as export_module
    importlib.reload(export_module)
    import backend.routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, service_module.schedule_service


def test_export_ics(tmp_path):
    client, svc = setup_app(tmp_path)

    act_id = svc.create_activity("Practice", 1.0, "music")
    svc.schedule_activity(1, "2024-01-01", 4, act_id)

    resp = client.get("/schedule/export/ics", params={"user_id": 1, "date": "2024-01-01"})
    assert resp.status_code == 200
    text = resp.text
    assert "BEGIN:VCALENDAR" in text
    assert "SUMMARY:Practice" in text
    assert "DTSTART:20240101T010000" in text
    assert "DTEND:20240101T020000" in text
