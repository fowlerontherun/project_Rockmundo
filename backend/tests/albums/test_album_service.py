import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.music import Base as MusicBase, Release
from backend.services.album_service import AlbumService
from backend.services.band_service import Base as BandBase, BandService, Band, BandCollaboration


def get_services():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    BandBase.metadata.create_all(bind=engine)
    # Make band tables visible in the music metadata so foreign keys resolve
    # when creating release/track tables.
    Band.__table__.tometadata(MusicBase.metadata)
    BandCollaboration.__table__.tometadata(MusicBase.metadata)
    MusicBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    band_svc = BandService(SessionLocal)
    album_svc = AlbumService(SessionLocal, band_svc)
    return album_svc, band_svc, SessionLocal


def test_ep_track_limit():
    album_svc, band_svc, _ = get_services()
    band = band_svc.create_band(user_id=1, band_name="Band", genre="rock")
    data = {
        "band_id": band.id,
        "title": "Too Many Tracks",
        "format": "ep",
        "tracks": [{"title": f"T{i}", "duration": 120} for i in range(5)],
    }
    with pytest.raises(ValueError):
        album_svc.create_release(data)


def test_publish_release_sets_date_and_returns_earnings():
    album_svc, band_svc, SessionLocal = get_services()
    band = band_svc.create_band(user_id=1, band_name="Band", genre="rock")
    data = {
        "band_id": band.id,
        "title": "LP1",
        "format": "lp",
        "tracks": [{"title": "Song1", "duration": 120}],
    }
    res = album_svc.create_release(data)
    result = album_svc.publish_release(res["release_id"])
    assert result["status"] == "ok"
    assert result["revenue"] == 1000
    with SessionLocal() as session:
        release = session.get(Release, res["release_id"])
        assert release.release_date is not None


def test_collaboration_publish_split():
    album_svc, band_svc, _ = get_services()
    band1 = band_svc.create_band(user_id=1, band_name="Band1", genre="rock")
    band2 = band_svc.create_band(user_id=2, band_name="Band2", genre="jazz")
    collab = band_svc.create_collaboration(band1.id, band2.id, "album", "Collab")
    data = {
        "band_id": band1.id,
        "title": "Collab Album",
        "format": "lp",
        "tracks": [{"title": "Song", "duration": 120}],
        "collaboration_id": collab.id,
    }
    res = album_svc.create_release(data)
    result = album_svc.publish_release(res["release_id"])
    assert result["earnings"]["band_1_share"] == 500
    assert result["earnings"]["band_2_share"] == 500


def test_live_album_yearly_limit_and_format_restriction():
    album_svc, band_svc, _ = get_services()
    band = band_svc.create_band(user_id=1, band_name="Band", genre="rock")

    data = {
        "band_id": band.id,
        "title": "Live One",
        "format": "lp",
        "album_type": "live",
        "tracks": [{"title": "Jam", "duration": 120}],
    }
    res = album_svc.create_release(data)
    album_svc.publish_release(res["release_id"])

    with pytest.raises(ValueError):
        album_svc.create_release(data)

    bad = {
        "band_id": band.id,
        "title": "Live EP",
        "format": "ep",
        "album_type": "live",
        "tracks": [{"title": "Jam", "duration": 120}],
    }
    with pytest.raises(ValueError):
        album_svc.create_release(bad)

