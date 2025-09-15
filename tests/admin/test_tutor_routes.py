import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, Request

BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from routes.admin_tutor_routes import (  # type: ignore  # noqa: E402,I001
    TutorIn,
    create_tutor,
    delete_tutor,
    list_tutors,
    update_tutor,
    svc,
)


def test_tutor_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    payload = TutorIn(
        name="Maestro",
        specialization="guitar",
        hourly_rate=50,
        level_requirement=10,
    )
    with pytest.raises(HTTPException):
        asyncio.run(list_tutors(req))
    with pytest.raises(HTTPException):
        asyncio.run(create_tutor(payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(update_tutor(1, payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_tutor(1, req))


def test_tutor_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "routes.admin_tutor_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "routes.admin_tutor_routes.require_permission", fake_require_permission
    )

    svc.db_path = str(tmp_path / "tutors.db")
    svc.ensure_schema()
    svc.clear()

    req = Request({"type": "http", "headers": []})
    payload = TutorIn(
        name="Maestro",
        specialization="guitar",
        hourly_rate=50,
        level_requirement=10,
    )
    tutor = asyncio.run(create_tutor(payload, req))
    assert tutor.id is not None

    tutors = asyncio.run(list_tutors(req))
    assert len(tutors) == 1

    upd = TutorIn(
        name="Master",
        specialization="drums",
        hourly_rate=60,
        level_requirement=5,
    )
    updated = asyncio.run(update_tutor(tutor.id, upd, req))
    assert updated.name == "Master"
    assert updated.specialization == "drums"

    res = asyncio.run(delete_tutor(tutor.id, req))
    assert res == {"status": "deleted"}
    assert asyncio.run(list_tutors(req)) == []
