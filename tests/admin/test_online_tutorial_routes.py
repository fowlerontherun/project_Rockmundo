import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, Request

# Allow importing the backend package and its auth helpers
BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from routes.admin_online_tutorial_routes import (  # type: ignore
    OnlineTutorialIn,
    create_tutorial,
    delete_tutorial,
    list_tutorials,
    update_tutorial,
    svc,
)


def test_online_tutorial_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    payload = OnlineTutorialIn(
        video_url="https://example.com",
        skill="guitar",
        xp_rate=5,
        plateau_level=10,
        rarity_weight=1,
    )
    with pytest.raises(HTTPException):
        asyncio.run(list_tutorials(req))
    with pytest.raises(HTTPException):
        asyncio.run(create_tutorial(payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(update_tutorial(1, payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_tutorial(1, req))


def test_online_tutorial_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "routes.admin_online_tutorial_routes.get_current_user_id",
        fake_current_user,
    )
    monkeypatch.setattr(
        "routes.admin_online_tutorial_routes.require_permission", fake_require_permission
    )

    svc.db_path = str(tmp_path / "tutorials.db")
    svc.ensure_schema()
    svc.clear()

    req = Request({"type": "http", "headers": []})
    payload = OnlineTutorialIn(
        video_url="https://example.com",
        skill="guitar",
        xp_rate=5,
        plateau_level=10,
        rarity_weight=1,
    )
    tutorial = asyncio.run(create_tutorial(payload, req))
    assert tutorial.id is not None

    tutorials = asyncio.run(list_tutorials(req))
    assert len(tutorials) == 1

    upd = OnlineTutorialIn(
        video_url="https://example.com/2",
        skill="drums",
        xp_rate=6,
        plateau_level=12,
        rarity_weight=2,
    )
    updated = asyncio.run(update_tutorial(tutorial.id, upd, req))
    assert updated.skill == "drums"
    assert updated.video_url.endswith("/2")

    res = asyncio.run(delete_tutorial(tutorial.id, req))
    assert res == {"status": "deleted"}
    assert asyncio.run(list_tutorials(req)) == []
