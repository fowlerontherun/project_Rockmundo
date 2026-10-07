from fastapi import FastAPI

from routes import song_catalogue_routes


class StubBandService:
    def __init__(self):
        self.allowed = {7: {1, 2}}

    def get_band_info(self, band_id):
        members = self.allowed.get(band_id)
        if members is None:
            return None
        return {
            "id": band_id,
            "members": [{"user_id": user_id, "role": "member"} for user_id in members],
        }


class StubSongService:
    def __init__(self):
        self.created = []

    def create_song(self, data):
        self.created.append(data)
        return {"status": "ok", "song_id": 101}

    def list_songs_by_band(self, band_id, search=None, sort=None):
        return [
            {
                "song_id": 101,
                "title": "Finished Song",
                "duration": 205,
                "genre": "rock",
                "plays": 0,
                "quality_score": 74,
                "writing_minutes": 150,
                "polish_attempted": True,
                "polish_skipped": False,
                "polish_succeeded": True,
                "polish_bonus": 5,
            }
        ]

    def get_song(self, song_id):
        if song_id != 101:
            return None
        return {
            "song_id": 101,
            "band_id": 7,
            "title": "Finished Song",
            "duration": 205,
            "genre": "rock",
            "plays": 0,
            "quality_score": 74,
            "writing_minutes": 150,
            "polish_attempted": True,
            "polish_skipped": False,
            "polish_succeeded": True,
            "polish_bonus": 5,
        }

    def get_songwriting_metadata(self, song_id):
        if song_id != 101:
            return None
        return {
            "song_id": 101,
            "draft_id": 9,
            "quality_score": 74,
            "writing_minutes": 150,
            "lyrics": "finished lyrics",
        }


def _app(client_factory, user_id, monkeypatch):
    band_service = StubBandService()
    song_service = StubSongService()
    monkeypatch.setattr(song_catalogue_routes, "band_service", band_service)
    monkeypatch.setattr(song_catalogue_routes, "song_service", song_service)

    app = FastAPI()
    app.include_router(song_catalogue_routes.router)
    client = client_factory(
        app,
        {song_catalogue_routes.get_current_user_id: lambda: user_id},
    )
    return client, song_service


def test_band_song_catalogue_exposes_writing_quality(client_factory, monkeypatch):
    client, _ = _app(client_factory, 1, monkeypatch)

    response = client.get("/songs/band/7?sort=quality")
    assert response.status_code == 200
    songs = response.json()
    assert songs[0]["quality_score"] == 74
    assert songs[0]["writing_minutes"] == 150
    assert songs[0]["polish_succeeded"] is True


def test_song_detail_includes_songwriting_metadata(client_factory, monkeypatch):
    client, _ = _app(client_factory, 1, monkeypatch)

    response = client.get("/songs/101")
    assert response.status_code == 200
    payload = response.json()
    assert payload["songwriting"]["draft_id"] == 9
    assert payload["songwriting"]["quality_score"] == 74


def test_song_catalogue_rejects_other_band_member(client_factory, monkeypatch):
    client, _ = _app(client_factory, 99, monkeypatch)

    response = client.get("/songs/band/7")
    assert response.status_code == 403
    assert response.json()["detail"] == "band_membership_required"


def test_direct_song_creation_uses_current_user_royalty_owner(client_factory, monkeypatch):
    client, song_service = _app(client_factory, 1, monkeypatch)

    response = client.post(
        "/songs",
        json={
            "band_id": 7,
            "title": "Manual Song",
            "duration_sec": 180,
            "genre": "rock",
            "lyrics": "lyrics",
            "themes": ["love"],
        },
    )
    assert response.status_code == 200
    assert response.json()["song_id"] == 101
    assert song_service.created[0]["royalties_split"] == {1: 100}
