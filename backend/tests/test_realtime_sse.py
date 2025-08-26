# backend/tests/test_realtime_sse.py
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

def _iter_sse_lines(resp):
    # Helper: yields decoded lines from the streaming response iterator
    for chunk in resp.iter_content(chunk_size=None):
        if not chunk:
            continue
        for line in chunk.decode("utf-8").splitlines():
            yield line

def test_sse_user_and_pulse(app_fixture):
    client = TestClient(app_fixture)

    # Start SSE with user 42, subscribe to pulse as well
    with client.stream("GET", "/realtime/sse?topics=pulse", headers={"X-User-Id": "42"}) as resp:
        assert resp.status_code == 200
        lines = []

        # Consume the initial hello
        for line in _iter_sse_lines(resp):
            lines.append(line)
            if line.strip() == "":
                break

        assert any(line.startswith("event: hello") for line in lines)
        assert any(line.startswith("data: ") for line in lines)
        payload_lines = [l[6:] for l in lines if l.startswith("data: ")]
        joined = "\n".join(payload_lines)
        hello = json.loads(joined)
        assert "subscribed" in hello["data"]

        # Publish events
        from asyncio import get_event_loop
        get_event_loop().run_until_complete(publish_mail_unread(42, unread_count=9))
        get_event_loop().run_until_complete(publish_pulse_update({"top": [{"name": "Band Z", "score": 777}] }))

        # Read until we see both events
        got_user = False
        got_pulse = False
        message_block = []
        for line in _iter_sse_lines(resp):
            if line.strip() == "":
                # end of one event block
                if any(l.startswith("event: message") for l in message_block):
                    data_lines = [l[6:] for l in message_block if l.startswith("data: ")]
                    msg = json.loads("\n".join(data_lines))
                    if msg["topic"] == "user:42" and msg["data"]["type"] == "mail_unread":
                        got_user = True
                    if msg["topic"] == "pulse" and msg["data"]["type"] == "pulse_tick":
                        got_pulse = True
                message_block = []
                if got_user and got_pulse:
                    break
            else:
                message_block.append(line)

        assert got_user, "Did not receive user:42 mail_unread SSE"
        assert got_pulse, "Did not receive pulse tick SSE"
