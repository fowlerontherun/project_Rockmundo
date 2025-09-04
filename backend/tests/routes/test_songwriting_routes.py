import asyncio
from fastapi import FastAPI
from backend.routes import songwriting_routes
from backend.services.songwriting_service import SongwritingService
from backend.services.originality_service import OriginalityService


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
