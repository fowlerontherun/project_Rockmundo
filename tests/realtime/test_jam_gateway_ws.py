from fastapi.testclient import TestClient


def test_jam_gateway_ping_and_stream(jam_app):
    app, service = jam_app
    client = TestClient(app)
    with client.websocket_connect("/jam/ws/s1") as ws:
        joined = ws.receive_json()
        assert joined == {"type": "joined", "user_id": 1}
        assert service.sessions == {"s1": {1}}

        ws.send_json({"op": "ping"})
        assert ws.receive_json() == {"op": "pong"}

        ws.send_json(
            {"op": "start_stream", "stream_id": "sA", "codec": "opus", "premium": True}
        )
        started = ws.receive_json()
        assert started["type"] == "stream_started"
        assert started["user_id"] == 1
        assert started["stream"]["stream_id"] == "sA"

        ws.send_json({"op": "pause_stream"})
        paused = ws.receive_json()
        assert paused == {"type": "stream_paused", "user_id": 1}
        assert service.streams[("s1", 1)].paused is True

        ws.send_json({"op": "resume_stream"})
        resumed = ws.receive_json()
        assert resumed == {"type": "stream_resumed", "user_id": 1}
        assert service.streams[("s1", 1)].paused is False

        ws.send_json({"op": "stop_stream"})
        stopped = ws.receive_json()
        assert stopped == {"type": "stream_stopped", "user_id": 1}
        assert ("s1", 1) not in service.streams

    assert service.sessions == {}
    assert service.streams == {}
    assert service.invites == {}


def test_jam_gateway_invite(jam_app):
    app, service = jam_app
    client = TestClient(app)
    with client.websocket_connect("/jam/ws/s1") as ws:
        ws.receive_json()
        ws.send_json({"op": "invite", "invitee_id": 2})
        invited = ws.receive_json()
        assert invited == {"type": "invited", "user_id": 2}
        assert service.invites == {"s1": {2}}

    assert service.invites == {}
    assert service.sessions == {}
