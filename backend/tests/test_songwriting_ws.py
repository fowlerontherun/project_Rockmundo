import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI

Path(__file__).resolve().parents[1].joinpath("database").mkdir(exist_ok=True)

from backend.routes import songwriting_routes  # noqa: E402
from services.originality_service import OriginalityService  # noqa: E402
from services.songwriting_service import SongwritingService  # noqa: E402


class FakeLLM:
    async def complete(self, history):
        return "la"


def _make_app(svc: SongwritingService) -> FastAPI:
    songwriting_routes.songwriting_service = svc
    app = FastAPI()
    app.include_router(songwriting_routes.router)
    return app


def test_ws_requires_auth(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    app = _make_app(svc)
    client = client_factory(app)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/songwriting/ws/{draft.id}"):
            pass


def test_ws_denies_non_participants(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    app = _make_app(svc)
    client = client_factory(
        app, {songwriting_routes.get_current_user_id: lambda: 2}
    )
    with pytest.raises(Exception):
        with client.websocket_connect(f"/songwriting/ws/{draft.id}"):
            pass
