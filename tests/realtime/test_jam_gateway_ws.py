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
    def join_session(self, session_id: str, user_id: int) -> None:  # pragma: no cover - trivial
        pass

    def leave_session(self, session_id: str, user_id: int) -> None:  # pragma: no cover - trivial
        pass

    def start_stream(
        self, session_id: str, user_id: int, stream_id: str, codec: str, premium: bool = False
    ):
        return FakeStream(user_id, stream_id, codec, premium)

    def stop_stream(self, session_id: str, user_id: int) -> None:  # pragma: no cover - trivial
        pass


# Inject our fake JamService module before importing the gateway
fake_module = types.ModuleType("jam_service")
fake_module.JamService = FakeJamService
sys.modules["backend.services.jam_service"] = fake_module

from backend.realtime import jam_gateway  # noqa: E402


def create_app() -> FastAPI:
    app = FastAPI()
    jam_gateway.jam_service = FakeJamService()
    app.include_router(jam_gateway.router)
    return app


def test_jam_gateway_ping_and_stream():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/jam/ws/s1", headers={"X-User-Id": "1"}) as ws:
        joined = ws.receive_json()
        assert joined == {"type": "joined", "user_id": 1}
        ws.send_json({"op": "ping"})
        assert ws.receive_json() == {"op": "pong"}
        ws.send_json({"op": "start_stream", "stream_id": "sA", "codec": "opus", "premium": True})
        started = ws.receive_json()
        assert started["type"] == "stream_started"
        assert started["user_id"] == 1
        assert started["stream"]["stream_id"] == "sA"

