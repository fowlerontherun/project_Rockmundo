import asyncio
from pathlib import Path

from fastapi import FastAPI

Path(__file__).resolve().parents[2].joinpath("database").mkdir(exist_ok=True)

from routes import songwriting_routes  # noqa: E402
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


def test_edit_draft_invalid_themes_route(client_factory):
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
    resp = client.put(
        f"/songwriting/drafts/{draft.id}",
        json={"themes": ["only", "two"]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["msg"].endswith("exactly_three_themes_required")
    resp2 = client.put(
        f"/songwriting/drafts/{draft.id}",
        json={"themes": ["x", "y", "invalid"]},
    )
    assert resp2.status_code == 422
    assert resp2.json()["detail"][0]["msg"].endswith("unknown_theme")

def test_complete_route_notifies_all_songwriters_once(client_factory, monkeypatch):
    class StubRandom:
        def randint(self, low, high):
            return 55

    class RecordingNotifications:
        def __init__(self):
            self.sent = []

        def create(self, **kwargs):
            self.sent.append(kwargs)
            return len(self.sent)

    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    svc.rng = StubRandom()
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="Finished Song",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
    recorder = RecordingNotifications()
    monkeypatch.setattr(songwriting_routes, "songwriting_service", svc)
    monkeypatch.setattr(songwriting_routes, "notifications", recorder)

    app = FastAPI()
    app.include_router(songwriting_routes.router)
    client = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 1})

    first = client.post(f"/songwriting/drafts/{draft.id}/complete")
    assert first.status_code == 200
    payload = first.json()
    assert payload["quality_score"] == 50
    assert payload["polish"]["success_chance"] == 55
    assert {item["user_id"] for item in recorder.sent} == {1, 2}
    assert all(item["type_"] == "songwriting_complete" for item in recorder.sent)
    assert all("Song quality: 50/100" in item["body"] for item in recorder.sent)
    assert all("Writing time: 1h" in item["body"] for item in recorder.sent)

    second = client.post(f"/songwriting/drafts/{draft.id}/complete")
    assert second.status_code == 200
    assert second.json()["newly_completed"] is False
    assert len(recorder.sent) == 2

def test_accepted_co_writer_can_fetch_draft(client_factory):
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="Shared Draft",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
    songwriting_routes.songwriting_service = svc

    app = FastAPI()
    app.include_router(songwriting_routes.router)
    client = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 2})

    resp = client.get(f"/songwriting/drafts/{draft.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == draft.id

def test_finalize_route_creates_song_and_notifies_once(client_factory, monkeypatch):
    class StubBandService:
        def get_band_info(self, band_id):
            return {
                "id": band_id,
                "members": [{"user_id": 1, "role": "founder"}],
            }

    class StubSongService:
        def __init__(self):
            self.created = []
            self.metadata_by_draft = {}

        def get_songwriting_metadata_by_draft(self, draft_id):
            return self.metadata_by_draft.get(draft_id)

        def create_song(self, data):
            song_id = len(self.created) + 100
            self.created.append(data)
            meta = dict(data["songwriting_metadata"])
            meta["song_id"] = song_id
            self.metadata_by_draft[meta["draft_id"]] = meta
            return {"status": "ok", "song_id": song_id}

    class RecordingNotifications:
        def __init__(self):
            self.sent = []

        def create(self, **kwargs):
            self.sent.append(kwargs)
            return len(self.sent)

    song_store = StubSongService()
    svc = SongwritingService(
        llm_client=FakeLLM(),
        originality=OriginalityService(),
        band_service=StubBandService(),
        song_service=song_store,
    )
    draft = asyncio.run(
        svc.generate_draft(
            creator_id=1,
            title="Catalogue Song",
            genre="rock",
            themes=["x", "y", "z"],
        )
    )
    svc.complete_song(draft.id, user_id=1)
    svc.skip_polish(draft.id, user_id=1)

    recorder = RecordingNotifications()
    monkeypatch.setattr(songwriting_routes, "songwriting_service", svc)
    monkeypatch.setattr(songwriting_routes, "notifications", recorder)

    app = FastAPI()
    app.include_router(songwriting_routes.router)
    client = client_factory(app, {songwriting_routes.get_current_user_id: lambda: 1})

    first = client.post(
        f"/songwriting/drafts/{draft.id}/finalize",
        json={
            "band_id": 7,
            "duration_sec": 205,
            "distribution_channels": ["digital", "streaming"],
        },
    )
    assert first.status_code == 200
    assert first.json()["already_finalized"] is False
    assert len(song_store.created) == 1
    assert song_store.created[0]["songwriting_metadata"]["quality_score"] == 50
    assert song_store.created[0]["songwriting_metadata"]["polish_skipped"] is True
    assert song_store.created[0]["songwriting_metadata"]["distribution_channels"] == [
        "digital",
        "streaming",
    ]
    assert len(recorder.sent) == 1
    assert recorder.sent[0]["type_"] == "songwriting_finalized"

    retry = client.post(
        f"/songwriting/drafts/{draft.id}/finalize",
        json={
            "band_id": 7,
            "duration_sec": 205,
            "distribution_channels": ["digital"],
        },
    )
    assert retry.status_code == 200
    assert retry.json()["already_finalized"] is True
    assert retry.json()["song_id"] == first.json()["song_id"]
    assert len(song_store.created) == 1
    assert len(recorder.sent) == 1

