import asyncio
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.realtime import admin_gateway
from backend.realtime.admin_gateway import router as admin_router, publish_economy_alert


@pytest.fixture(autouse=True)
def stub_permissions(monkeypatch):
    async def fake_require_permission(roles, user_id):
        if user_id != 1:
            raise Exception("forbidden")
        return True

    monkeypatch.setattr(admin_gateway, "require_permission", fake_require_permission)

@pytest.fixture
def app_fixture():
    app = FastAPI()
    app.include_router(admin_router)
    return app


def test_ws_requires_admin(app_fixture):
    client = TestClient(app_fixture)

    # No auth header -> should fail
    with pytest.raises(Exception):
        with client.websocket_connect("/admin/realtime/ws"):
            pass

    # Non-admin user -> should fail
    with pytest.raises(Exception):
        with client.websocket_connect("/admin/realtime/ws", headers={"X-User-Id": "2"}):
            pass


def test_admin_receives_alert(app_fixture):
    client = TestClient(app_fixture)

    with client.websocket_connect("/admin/realtime/ws", headers={"X-User-Id": "1"}) as ws:
        ws.send_text(json.dumps({"op": "subscribe", "topics": ["economy"]}))
        ok = json.loads(ws.receive_text())
        assert ok.get("ok") is True

        asyncio.get_event_loop().run_until_complete(publish_economy_alert({"value": 1}))
        msg = json.loads(ws.receive_text())
        assert msg["topic"] == "admin:economy"
        assert msg["data"]["type"] == "economy_alert"
