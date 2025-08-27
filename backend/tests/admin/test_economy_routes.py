import asyncio
import asyncio
import pytest
from fastapi import HTTPException, Request

from backend.routes import admin_economy_routes as routes
from backend.services.economy_service import EconomyService
from backend.models.economy_config import set_config, EconomyConfig


def test_admin_economy_routes_require_admin():
    req = Request({})
    with pytest.raises(HTTPException):
        asyncio.run(routes.get_config(req))
    with pytest.raises(HTTPException):
        asyncio.run(routes.update_config({}, req))
    with pytest.raises(HTTPException):
        asyncio.run(routes.recent_transactions(req))


def test_admin_economy_config_updates(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_role(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_economy_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_economy_routes.require_role", fake_require_role
    )

    db_file = tmp_path / "econ.db"
    config_file = tmp_path / "config.json"
    svc = EconomyService(str(db_file))
    svc.ensure_schema()
    routes.svc.economy_service = svc
    routes.svc.config_path = config_file
    set_config(EconomyConfig())

    req = Request({})
    asyncio.run(routes.update_config(routes.ConfigUpdateIn(tax_rate=0.1), req))
    # deposit 1000 cents should apply 10% tax -> 900
    svc.deposit(1, 1000)
    assert svc.get_balance(1) == 900
    txns = asyncio.run(routes.recent_transactions(req))
    assert len(txns) == 1
    assert txns[0].type == "deposit"
