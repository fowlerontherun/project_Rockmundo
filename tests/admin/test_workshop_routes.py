import asyncio
import sys
from pathlib import Path

# isort: skip_file

import pytest
from fastapi import HTTPException, Request

# allow import backend
BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from backend.routes.admin_workshop_routes import (  # type: ignore  # noqa: E402
    WorkshopIn,
    create_workshop,
    delete_workshop,
    list_workshops,
    update_workshop,
    svc,
)  # isort: skip


def test_workshop_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    payload = WorkshopIn(
        skill_target="guitar",
        xp_reward=10,
        ticket_price=100,
        schedule="2024-01-01T00:00:00Z",
    )
    with pytest.raises(HTTPException):
        asyncio.run(list_workshops(req))
    with pytest.raises(HTTPException):
        asyncio.run(create_workshop(payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(update_workshop(1, payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_workshop(1, req))


def test_workshop_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_workshop_routes.get_current_user_id",
        fake_current_user,
    )
    monkeypatch.setattr(
        "backend.routes.admin_workshop_routes.require_permission",
        fake_require_permission,
    )

    svc.db_path = str(tmp_path / "workshops.db")
    svc.ensure_schema()
    svc.clear()

    req = Request({"type": "http", "headers": []})
    payload = WorkshopIn(
        skill_target="guitar",
        xp_reward=10,
        ticket_price=100,
        schedule="2024-01-01T00:00:00Z",
    )
    ws = asyncio.run(create_workshop(payload, req))
    assert ws.id is not None

    workshops = asyncio.run(list_workshops(req))
    assert len(workshops) == 1

    upd = WorkshopIn(
        skill_target="drums",
        xp_reward=20,
        ticket_price=150,
        schedule="2024-02-02T00:00:00Z",
    )
    updated = asyncio.run(update_workshop(ws.id, upd, req))
    assert updated.skill_target == "drums"
    assert updated.xp_reward == 20

    res = asyncio.run(delete_workshop(ws.id, req))
    assert res == {"status": "deleted"}
    assert asyncio.run(list_workshops(req)) == []
