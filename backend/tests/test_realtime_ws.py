# backend/tests/test_realtime_ws.py
import asyncio
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.realtime.gateway import router as realtime_router
from backend.realtime.publish import publish_mail_unread, publish_pulse_update

@pytest.fixture
def app_fixture():
    app = FastAPI()
    app.include_router(realtime_router)
    return app

def test_ws_requires_auth(app_fixture):
    client = TestClient(app_fixture)
    # Expect connection to fail or close immediately without auth
    with pytest.raises(Exception):
        with client.websocket_connect("/realtime/ws"):
            pass

def test_ws_user_scoping(app_fixture):
    client = TestClient(app_fixture)

    # Connect as user 1
    with client.websocket_connect("/realtime/ws", headers={"X-User-Id": "1"}) as ws1:
        ws1.send_text(json.dumps({"op": "subscribe", "topics": ["pulse"]}))
        ok1 = json.loads(ws1.receive_text())
        assert ok1.get("ok") is True

        # Connect as user 2
        with client.websocket_connect("/realtime/ws", headers={"X-User-Id": "2"}) as ws2:
            ws2.send_text(json.dumps({"op": "subscribe", "topics": ["pulse"]}))
            ok2 = json.loads(ws2.receive_text())
            assert ok2.get("ok") is True

            # Publish a mail_unread for user 1 only
            asyncio.get_event_loop().run_until_complete(publish_mail_unread(1, unread_count=5))

            # ws1 should receive user:1 event
            msg1 = json.loads(ws1.receive_text(timeout=2.0))
            assert msg1["topic"] == "user:1"
            assert msg1["data"]["type"] == "mail_unread"
            assert msg1["data"]["unread"] == 5

            # ws2 should NOT receive that user:1 event.
            with pytest.raises(Exception):
                _ = ws2.receive_text(timeout=0.2)

            # Publish a pulse broadcast
            asyncio.get_event_loop().run_until_complete(
                publish_pulse_update({"top": [{"name": "Band A", "score": 123}]})
            )

            # Both should get the pulse tick
            got_pulse1 = json.loads(ws1.receive_text(timeout=2.0))
            got_pulse2 = json.loads(ws2.receive_text(timeout=2.0))
            assert got_pulse1["topic"] == "pulse"
            assert got_pulse2["topic"] == "pulse"
