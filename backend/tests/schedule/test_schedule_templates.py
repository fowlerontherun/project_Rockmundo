import importlib
import importlib
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "templates.db"
    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as ds_model
    from models import default_schedule as def_model
    from models import default_schedule_templates as tmpl_model

    activity_model.DB_PATH = db_file
    ds_model.DB_PATH = db_file
    def_model.DB_PATH = db_file
    tmpl_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_service_module
    importlib.reload(schedule_service_module)
    import backend.routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_service_module.schedule_service


def test_create_and_apply_template(tmp_path):
    client, svc = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 1, "music")

    resp = client.post(
        "/schedule/templates/1",
        json={"name": "morning", "entries": [{"hour": 9, "activity_id": act_id}]},
    )
    assert resp.status_code == 200
    template_id = resp.json()["id"]

    resp = client.get("/schedule/templates/1")
    assert resp.status_code == 200
    data = resp.json()
    assert any(t["id"] == template_id for t in data["templates"])

    resp = client.post(f"/schedule/apply-template/1/2024-01-01/{template_id}")
    assert resp.status_code == 200

    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT activity_id FROM daily_schedule WHERE user_id=1 AND date='2024-01-01' AND slot=36"
        )
        row = cur.fetchone()
        assert row and row[0] == act_id
