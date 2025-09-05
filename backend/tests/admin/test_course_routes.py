import asyncio
import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_course_routes import (
    CourseIn,
    create_course,
    delete_course,
    list_courses,
    update_course,
    svc,
)


def sample_course() -> CourseIn:
    return CourseIn(skill_target="guitar", duration=10, prestige=False)


def test_course_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    with pytest.raises(HTTPException):
        asyncio.run(create_course(sample_course(), req))
    with pytest.raises(HTTPException):
        asyncio.run(update_course(1, sample_course(), req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_course(1, req))


def test_course_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_course_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_course_routes.require_permission", fake_require_permission
    )

    svc.db_path = str(tmp_path / "courses.db")
    svc.ensure_schema()

    req = Request({"type": "http", "headers": []})
    created = asyncio.run(create_course(sample_course(), req))
    assert created.id > 0
    listed = asyncio.run(list_courses(req))
    assert len(listed) == 1
    updated = asyncio.run(
        update_course(created.id, CourseIn(skill_target="piano", duration=12), req)
    )
    assert updated.skill_target == "piano"
    asyncio.run(delete_course(created.id, req))
    assert asyncio.run(list_courses(req)) == []
