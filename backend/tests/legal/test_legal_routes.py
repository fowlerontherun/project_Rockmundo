import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[3]))

from routes import legal_routes
from backend.services.economy_service import EconomyService
from backend.services.legal_service import LegalService
from backend.services.karma_service import KarmaService


class KarmaDB:
    def __init__(self):
        self.totals = {}
        self.events = []

    def insert_karma_event(self, event):
        self.events.append(event)

    def update_user_karma(self, user_id, amount):
        self.totals[user_id] = self.totals.get(user_id, 0) + amount

    def get_user_karma_total(self, user_id):
        return self.totals.get(user_id, 0)


def create_app(tmp_path):
    db = tmp_path / "test.db"
    economy = EconomyService(str(db))
    economy.ensure_schema()
    karma = KarmaService(KarmaDB())
    legal_routes._economy = economy
    legal_routes._karma = karma
    legal_routes.svc = LegalService(economy, karma)
    app = FastAPI()
    app.include_router(legal_routes.router)
    return app, economy, karma


def test_route_flow(tmp_path):
    app, economy, karma = create_app(tmp_path)
    client = TestClient(app)
    economy.deposit(2, 1000)
    r = client.post(
        "/legal/cases/create",
        json={"plaintiff_id": 1, "defendant_id": 2, "description": "contract", "amount_cents": 500},
    )
    assert r.status_code == 200
    case_id = r.json()["id"]
    r = client.post("/legal/cases/file", json={"case_id": case_id, "filer_id": 2, "text": "defense"})
    assert r.status_code == 200
    r = client.post(
        "/legal/cases/verdict",
        json={"case_id": case_id, "decision": "guilty", "penalty_cents": 500},
    )
    assert r.status_code == 200
    assert economy.get_balance(1) == 500
    assert karma.get_user_karma(2) < 0
