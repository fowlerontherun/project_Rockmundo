import pathlib
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure the project root is on sys.path for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))


class FakeStream:
    def __init__(self, user_id: int, stream_id: str, codec: str, premium: bool):
        self.user_id = user_id
        self.stream_id = stream_id
        self.codec = codec
        self.premium = premium
        self.started_at = "now"


class FakeJamService:
    def __init__(self) -> None:
        self.sessions: dict[str, set[int]] = {}
        self.streams: dict[tuple[str, int], FakeStream] = {}

    def join_session(self, session_id: str, user_id: int) -> None:
        self.sessions.setdefault(session_id, set()).add(user_id)

    def leave_session(self, session_id: str, user_id: int) -> None:
        users = self.sessions.get(session_id)
        if users:
            users.discard(user_id)
            if not users:
                self.sessions.pop(session_id, None)

    def start_stream(
        self, session_id: str, user_id: int, stream_id: str, codec: str, premium: bool = False
    ) -> FakeStream:
        stream = FakeStream(user_id, stream_id, codec, premium)
        self.streams[(session_id, user_id)] = stream
        return stream

    def stop_stream(self, session_id: str, user_id: int) -> None:
        self.streams.pop((session_id, user_id), None)


# Inject our fake JamService module before importing the gateway
fake_module = types.ModuleType("jam_service")
fake_module.JamService = FakeJamService
sys.modules["backend.services.jam_service"] = fake_module

from backend.realtime import jam_gateway  # noqa: E402


def create_app() -> FastAPI:
    app = FastAPI()
    jam_gateway.jam_service = FakeJamService()
    app.include_router(jam_gateway.router)
    async def _uid() -> int:
        return 1
    app.dependency_overrides[jam_gateway.get_current_user_id_dep] = _uid
    return app


def test_jam_gateway_ping_and_stream():
    app = create_app()
    service = jam_gateway.jam_service
    client = TestClient(app)
    with client.websocket_connect("/jam/ws/s1") as ws:
        joined = ws.receive_json()
        assert joined == {"type": "joined", "user_id": 1}
        assert service.sessions == {"s1": {1}}

        ws.send_json({"op": "ping"})
        assert ws.receive_json() == {"op": "pong"}

        ws.send_json({"op": "start_stream", "stream_id": "sA", "codec": "opus", "premium": True})
        started = ws.receive_json()
        assert started["type"] == "stream_started"
        assert started["user_id"] == 1
        assert started["stream"]["stream_id"] == "sA"
        assert service.streams[("s1", 1)].stream_id == "sA"

        ws.send_json({"op": "stop_stream"})
        stopped = ws.receive_json()
        assert stopped == {"type": "stream_stopped", "user_id": 1}
        assert ("s1", 1) not in service.streams

    assert service.sessions == {}

