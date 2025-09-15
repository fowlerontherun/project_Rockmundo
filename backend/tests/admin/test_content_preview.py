import asyncio
from copy import deepcopy

import pytest
from fastapi import Request

from routes.admin_npc_routes import preview_npc, svc as npc_svc
from routes.admin_quest_routes import preview_quest, svc as quest_svc
from routes.admin_economy_routes import (
    preview_config,
    svc as econ_svc,
    ConfigUpdateIn,
)


async def _allow(req):
    return 1


async def _role(roles, user_id):
    return True


def test_preview_endpoints_do_not_persist(monkeypatch):
    monkeypatch.setattr(
        "routes.admin_npc_routes.get_current_user_id", _allow
    )
    monkeypatch.setattr("routes.admin_npc_routes.require_permission", _role)
    monkeypatch.setattr(
        "routes.admin_quest_routes.get_current_user_id", _allow
    )
    monkeypatch.setattr("routes.admin_quest_routes.require_permission", _role)
    monkeypatch.setattr(
        "routes.admin_economy_routes.get_current_user_id", _allow
    )
    monkeypatch.setattr("routes.admin_economy_routes.require_permission", _role)

    req = Request({})

    asyncio.run(
        preview_npc({"identity": "X", "npc_type": "merchant", "stats": {"activity": 1}}, req)
    )
    assert npc_svc.db._npcs == {}

    payload = {
        "name": "Quest",
        "initial_stage": "start",
        "stages": [{"id": "start", "description": "hi", "branches": {}}],
    }
    asyncio.run(preview_quest(payload, req))
    assert quest_svc.get_quest(1) is None

    before = deepcopy(econ_svc.get_config())
    asyncio.run(preview_config(ConfigUpdateIn(tax_rate=0.5), req))
    after = econ_svc.get_config()
    assert before == after
