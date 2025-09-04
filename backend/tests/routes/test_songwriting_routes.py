import asyncio
from pathlib import Path

from fastapi import FastAPI

Path(__file__).resolve().parents[2].joinpath("database").mkdir(exist_ok=True)

from backend.routes import songwriting_routes  # noqa: E402
from backend.services.originality_service import OriginalityService  # noqa: E402
from backend.services.songwriting_service import SongwritingService  # noqa: E402


class FakeLLM:
    async def complete(self, history):
        return "la"


def test_get_drafts_creator_and_co_writer(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    d1 = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    svc.add_co_writer(d1.id, user_id=1, co_writer_id=2)
    songwriting_routes.songwriting_service = svc
    app = FastAPI()
    app.include_router(songwriting_routes.router)

    c1 = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 1})
    r1 = c1.get("/songwriting/drafts")
    assert {d["id"] for d in r1.json()} == {d1.id}

    c2 = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 2})
    r2 = c2.get("/songwriting/drafts")
    assert {d["id"] for d in r2.json()} == {d1.id}


def test_add_co_writer_self_invite_route(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    songwriting_routes.songwriting_service = svc
    app = FastAPI()
    app.include_router(songwriting_routes.router)

    client = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 1})
    resp = client.post(
        f"/songwriting/drafts/{draft.id}/co_writers",
        json={"co_writer_id": 1},
    )
    assert resp.status_code == 400


def test_add_co_writer_duplicate_route(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    songwriting_routes.songwriting_service = svc
    app = FastAPI()
    app.include_router(songwriting_routes.router)

    client = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 1})
    first = client.post(
        f"/songwriting/drafts/{draft.id}/co_writers",
        json={"co_writer_id": 2},
    )
    assert first.status_code == 200
    dup = client.post(
        f"/songwriting/drafts/{draft.id}/co_writers",
        json={"co_writer_id": 2},
    )
    assert dup.status_code == 409
