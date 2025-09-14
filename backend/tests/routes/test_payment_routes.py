from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes import payment_routes
from services.economy_service import EconomyService
from services.payment_service import PaymentService


def create_app(tmp_path, succeed: bool = True):
    db = tmp_path / "test.db"
    economy = EconomyService(str(db))
    economy.ensure_schema()
    gateway = payment_routes.MockGateway(succeed=succeed)
    payment_routes._gateway = gateway
    payment_routes._economy = economy
    payment_routes.svc = PaymentService(gateway, economy)
    app = FastAPI()
    app.include_router(payment_routes.router)
    return app, economy, gateway


def test_purchase_and_callback(tmp_path):
    app, economy, _ = create_app(tmp_path, succeed=True)
    client = TestClient(app)
    r = client.post("/payment/purchase", json={"user_id": 1, "amount_cents": 500})
    assert r.status_code == 200
    pid = r.json()["payment_id"]
    r = client.post("/payment/callback", json={"payment_id": pid})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert economy.get_balance(1) > 0


def test_purchase_failure(tmp_path):
    app, economy, _ = create_app(tmp_path, succeed=False)
    client = TestClient(app)
    r = client.post("/payment/purchase", json={"user_id": 1, "amount_cents": 500})
    assert r.status_code == 200
    pid = r.json()["payment_id"]
    r = client.post("/payment/callback", json={"payment_id": pid})
    assert r.status_code == 400
    assert economy.get_balance(1) == 0
