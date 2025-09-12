import asyncio

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.auth.dependencies import require_permission
from backend.auth.permissions import Permissions


def test_unknown_permission_rejected():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(require_permission(["not_a_permission"], user_id=1))
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "UNKNOWN_PERMISSION"


def test_permissions_endpoint_lists_available_permissions():
    app = FastAPI()

    @app.get("/auth/permissions")
    def list_permissions():
        return {"permissions": [p.value for p in Permissions]}

    client = TestClient(app)
    resp = client.get("/auth/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["permissions"]) == {p.value for p in Permissions}
