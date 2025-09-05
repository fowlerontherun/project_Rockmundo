import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, Request

BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from backend.routes.admin_apprenticeship_routes import (  # type: ignore  # noqa: E402,I001
    ApprenticeshipIn,
    create_apprenticeship,
    delete_apprenticeship,
    list_apprenticeships,
    update_apprenticeship,
    svc,
)


def test_apprenticeship_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    payload = ApprenticeshipIn(
        student_id=1,
        mentor_id=2,
        mentor_type="player",
        skill_id=3,
        duration_days=7,
        level_requirement=0,
    )
    with pytest.raises(HTTPException):
        asyncio.run(list_apprenticeships(req))
    with pytest.raises(HTTPException):
        asyncio.run(create_apprenticeship(payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(update_apprenticeship(1, payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_apprenticeship(1, req))


def test_apprenticeship_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_apprenticeship_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_apprenticeship_routes.require_permission", fake_require_permission
    )

    svc.db_path = str(tmp_path / "apprenticeships.db")
    svc.ensure_schema()
    svc.clear()

    req = Request({"type": "http", "headers": []})
    payload = ApprenticeshipIn(
        student_id=1,
        mentor_id=2,
        mentor_type="player",
        skill_id=3,
        duration_days=7,
        level_requirement=0,
    )
    app = asyncio.run(create_apprenticeship(payload, req))
    assert app.id is not None

    apps = asyncio.run(list_apprenticeships(req))
    assert len(apps) == 1

    upd = ApprenticeshipIn(
        student_id=1,
        mentor_id=3,
        mentor_type="npc",
        skill_id=4,
        duration_days=10,
        level_requirement=5,
        status="active",
    )
    updated = asyncio.run(update_apprenticeship(app.id, upd, req))
    assert updated.mentor_id == 3
    assert updated.status == "active"

    res = asyncio.run(delete_apprenticeship(app.id, req))
    assert res == {"status": "deleted"}
    assert asyncio.run(list_apprenticeships(req)) == []
