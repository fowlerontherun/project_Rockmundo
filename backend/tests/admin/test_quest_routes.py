import asyncio
import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_quest_routes import create_quest, update_stage, svc


def sample_payload():
    return {
        "name": "Dragon Hunt",
        "initial_stage": "start",
        "stages": [
            {
                "id": "start",
                "description": "Start",
                "branches": {"go": "fight"},
            },
            {
                "id": "fight",
                "description": "Fight the dragon",
                "branches": {},
            },
        ],
    }


def test_admin_quest_routes_require_admin():
    req = Request({})
    with pytest.raises(HTTPException):
        asyncio.run(create_quest(sample_payload(), req))
    with pytest.raises(HTTPException):
        asyncio.run(update_stage(1, "start", {"description": "x"}, req))


def test_admin_quest_create_and_update(monkeypatch):
    async def fake_current_user(req):
        return 1

    async def fake_require_role(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_quest_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_quest_routes.require_role", fake_require_role
    )

    req = Request({})
    quest = asyncio.run(create_quest(sample_payload(), req))
    quest_id = quest["id"]
    updated = asyncio.run(
        update_stage(
            quest_id,
            "start",
            {"description": "New start", "branches": {"go": "fight"}},
            req,
        )
    )
    assert updated["description"] == "New start"
    stored = svc.get_quest(quest_id)
    assert stored["stages"]["start"]["description"] == "New start"
