import asyncio

import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_npc_routes import (
    create_npc,
    delete_npc,
    edit_npc,
    simulate_npc,
    svc,
)


def test_admin_npc_routes_require_admin():
    req = Request({})
    with pytest.raises(HTTPException):
        asyncio.run(create_npc({"identity": "x", "npc_type": "type"}, req))
    with pytest.raises(HTTPException):
        asyncio.run(edit_npc(1, {"identity": "y"}, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_npc(1, req))
    with pytest.raises(HTTPException):
        asyncio.run(simulate_npc(1, req))


def test_admin_npc_routes_flow(monkeypatch):
    async def fake_current_user(req):
        return 1

    async def fake_require_role(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_npc_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_npc_routes.require_role", fake_require_role
    )

    req = Request({})
    npc = asyncio.run(create_npc({"identity": "A", "npc_type": "merchant"}, req))
    npc_id = npc["id"]
    updated = asyncio.run(edit_npc(npc_id, {"identity": "B"}, req))
    assert updated["identity"] == "B"
    sim = asyncio.run(simulate_npc(npc_id, req))
    assert "fame_gain" in sim
    res = asyncio.run(delete_npc(npc_id, req))
    assert res == {"status": "deleted"}
    # ensure service removed npc
    assert svc.get_npc(npc_id) is None
