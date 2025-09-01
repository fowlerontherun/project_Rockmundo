import pathlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from backend.realtime import polling


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(polling.router)
    return app


def test_polling_vote_flow():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/encore/ws/rock", headers={"X-User-Id": "1"}) as ws:
        ws.send_json({"vote": "A"})
        message = ws.receive_json()
        assert message["type"] == "leaderboard"
        assert message["votes"] == {"A": 1}
