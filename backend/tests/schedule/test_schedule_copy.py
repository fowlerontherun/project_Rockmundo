import importlib
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "copy.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model
    from backend.models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    import backend.services.schedule_service as schedule_service_module
    importlib.reload(schedule_service_module)
    import routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, schedule_service_module.schedule_service


def test_copy_schedule(tmp_path):
    client, svc = setup_app(tmp_path)
    act_id = svc.create_activity("Practice", 1, "music")
    svc.schedule_activity(1, "2024-01-01", 36, act_id)

    resp = client.post(
        "/schedule/copy",
        json={
            "user_id": 1,
            "src_date": "2024-01-01",
            "dest_dates": ["2024-01-02", "2024-01-03"],
        },
    )
    assert resp.status_code == 200

    day2 = svc.get_daily_schedule(1, "2024-01-02")
    day3 = svc.get_daily_schedule(1, "2024-01-03")
    assert day2 == day3
    assert day2[0]["slot"] == 36
    assert day2[0]["activity"]["id"] == act_id
