import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, Request

BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from routes.admin_schema_routes import (  # type: ignore
    apprenticeship_schema,
    book_schema,
    course_schema,
    online_tutorial_schema,
    tutor_schema,
    workshop_schema,
)

SCHEMA_FUNCS = [
    book_schema,
    course_schema,
    online_tutorial_schema,
    tutor_schema,
    apprenticeship_schema,
    workshop_schema,
]


@pytest.mark.parametrize("func", SCHEMA_FUNCS)
def test_admin_schema_requires_admin(func):
    req = Request({"type": "http", "headers": []})
    with pytest.raises(HTTPException):
        asyncio.run(func(req))


@pytest.mark.parametrize("func", SCHEMA_FUNCS)
def test_admin_schema_available(monkeypatch, func):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "routes.admin_schema_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "routes.admin_schema_routes.require_permission", fake_require_permission
    )

    req = Request({"type": "http", "headers": []})
    schema = asyncio.run(func(req))
    props = schema.get("properties", {})
    assert {"xp_rate", "level_cap", "prerequisites"}.issubset(props.keys())
