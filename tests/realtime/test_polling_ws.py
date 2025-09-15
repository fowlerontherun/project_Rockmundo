import pathlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from realtime import polling


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(polling.router)
    async def _uid() -> int:
        return 1
    app.dependency_overrides[polling.get_current_user_id_dep] = _uid
    return app


def test_polling_vote_flow():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/encore/ws/rock") as ws:
        ws.send_json({"vote": "A"})
        message = ws.receive_json()
        assert message["type"] == "leaderboard"
        assert message["votes"] == {"A": 1}
