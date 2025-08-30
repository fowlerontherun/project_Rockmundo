import asyncio
from fastapi import Request

from backend.services.admin_audit_service import (
    get_admin_audit_service,
    audit_dependency,
)
from backend.routes import admin_media_moderation_routes as media_routes
from backend.models.economy_config import set_config, save_config, EconomyConfig


def test_log_action_and_query(tmp_path):
    svc = get_admin_audit_service()
    svc.db_path = str(tmp_path / "audit.db")
    svc.ensure_schema()
    svc.clear()
    svc.log_action(1, "create", "/x")
    svc.log_action(2, "delete", "/y")
    logs = svc.query()
    assert logs[0]["actor"] == 1
    assert logs[1]["action"] == "delete"
    assert svc.query(limit=1) == logs[:1]


def test_admin_route_logs_action(monkeypatch, tmp_path):
    async def fake_current_user(req: Request):
        return 99

    async def fake_require_role(roles, user_id):
        return True

    monkeypatch.setattr(media_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(media_routes, "require_role", fake_require_role)
    monkeypatch.setattr(
        "backend.services.admin_audit_service.get_current_user_id", fake_current_user
    )

    svc = get_admin_audit_service()
    svc.db_path = str(tmp_path / "audit.db")
    svc.ensure_schema()
    svc.clear()

    req = type("Req", (), {"method": "POST", "url": type("U", (), {"path": "/admin/media/flag/1"})()})()
    asyncio.run(audit_dependency(req, svc))
    asyncio.run(media_routes.flag_media(1, req))

    logs = svc.query()
    assert len(logs) == 1
    assert logs[0]["actor"] == 99
    assert logs[0]["action"] == "POST"
    assert logs[0]["resource"].endswith("/media/flag/1")
    # reset economy config for later tests
    cfg = EconomyConfig()
    set_config(cfg)
    save_config(cfg)
