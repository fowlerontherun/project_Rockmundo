import importlib
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database


def setup_app(tmp_path):
    db_file = tmp_path / "sim.db"
    database.DB_PATH = db_file
    database.init_db()

    from backend.models import activity as activity_model

    activity_model.DB_PATH = db_file

    import backend.services.activity_processor as ap_module
    importlib.reload(ap_module)

    import routes.schedule_routes as routes_module
    importlib.reload(routes_module)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, ap_module, activity_model


def test_plan_simulation(tmp_path):
    client, ap_module, activity_model = setup_app(tmp_path)
    act1 = activity_model.create_activity(
        "Practice", 1, "music", rewards_json=json.dumps({"xp": 20, "energy": -5})
    )
    act2 = activity_model.create_activity(
        "Rest", 1, "rest", rewards_json=json.dumps({"xp": 0, "energy": 10})
    )

    result = ap_module.simulate_plan(1, [{"activity_id": act1}, {"activity_id": act2}])
    assert result == {"xp": 20, "energy": 5}

    resp = client.post(
        "/schedule/simulate",
        json={"user_id": 1, "entries": [{"activity_id": act1}, {"activity_id": act2}]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"xp": 20, "energy": 5}
