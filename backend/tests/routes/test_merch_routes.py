from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.economy_service import EconomyService
from services.merch_service import MerchService
from services.payment_service import MockGateway, PaymentService

import auth.dependencies as auth_dep
from typing import List


def _fake_require_permission(_: List[str]):
    async def _noop() -> None:
        return None

    return _noop


auth_dep.require_permission = _fake_require_permission

from routes import merch_routes


def create_app(tmp_path):
    db = tmp_path / "test.db"
    economy = EconomyService(str(db))
    economy.ensure_schema()
    gateway = MockGateway(prefix="test")
    payments = PaymentService(gateway, economy)
    svc = MerchService(db_path=str(db), economy=economy, payments=payments)
    svc.ensure_schema()
    merch_routes.svc = svc
    app = FastAPI()
    app.include_router(merch_routes.router)
    return app, economy, gateway


def test_purchase_flow_invokes_payment_and_updates_economy(tmp_path):
    app, economy, gateway = create_app(tmp_path)
    client = TestClient(app)

    r = client.post(
        "/merch/products",
        json={"name": "Tour Hat", "category": "hat", "band_id": 42},
    )
    assert r.status_code == 200
    pid = r.json()["product_id"]

    r = client.post(
        "/merch/skus",
        json={"product_id": pid, "price_cents": 500, "stock_qty": 2},
    )
    assert r.status_code == 200
    sid = r.json()["sku_id"]

    economy.deposit(1, 2000)

    r = client.post(
        "/merch/purchase",
        json={"buyer_user_id": 1, "items": [{"sku_id": sid, "qty": 1}]},
    )
    assert r.status_code == 200

    assert gateway.counter == 1

    from backend.economy.models import Account, Transaction as Tx
    from sqlalchemy import select

    with economy.SessionLocal() as session:
        band_balance = (
            session.execute(
                select(Account.balance_cents).where(
                    Account.user_id == 42, Account.currency == "USD"
                )
            ).scalar_one()
        )
        withdrawal = session.execute(
            select(Tx.id)
            .join(Account, Tx.src_account_id == Account.id)
            .where(Account.user_id == 1, Tx.type == "withdrawal")
        ).first()

    assert band_balance == 500
    assert withdrawal is not None

    purchases = merch_routes.svc.payments.purchases
    assert len(purchases) == 1
    assert next(iter(purchases.values())).status == "completed"
