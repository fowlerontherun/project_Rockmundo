from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import marketing_ai_routes


def test_generate_and_accept_plan(monkeypatch):
    fake_plan = {
        "band_id": 1,
        "plan": [
            {
                "type": "radio",
                "date": "2030-01-01",
                "media_channel": "KEXP",
            }
        ],
    }

    def fake_generate(band_id: int):
        assert band_id == 1
        return fake_plan

    monkeypatch.setattr(marketing_ai_routes, "generate_promotion_plan", fake_generate)

    app = FastAPI()
    app.include_router(marketing_ai_routes.router)
    client = TestClient(app)

    r = client.post("/marketing_ai/plan", json={"band_id": 1})
    assert r.status_code == 200
    assert r.json() == fake_plan

    r2 = client.post("/marketing_ai/plan/accept", json=fake_plan)
    assert r2.status_code == 200
    promotions = r2.json()["promotions"]
    assert promotions[0]["type"] == "radio"
    assert promotions[0]["media_channel"] == "KEXP"
