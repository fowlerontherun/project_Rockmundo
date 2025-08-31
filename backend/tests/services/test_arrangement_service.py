from backend.models.song import Song
from backend.services.arrangement_service import ArrangementService
from backend.services.recording_service import RecordingService
from backend.services.economy_service import EconomyService


def test_arrangement_tracks_feed_recording(tmp_path):
    econ = EconomyService(db_path=tmp_path / "econ.db")
    econ.ensure_schema()
    econ.deposit(1, 10_000)
    recording = RecordingService(economy=econ)
    service = ArrangementService(recording=recording)

    song = Song(
        id=10,
        title="Test",
        duration_sec=180,
        genre_id=None,
        lyrics="",
        owner_band_id=1,
    )

    t1 = service.add_track(song, "guitar", "Alice")
    t2 = service.add_track(song, "drums", "Bob")

    tracks = service.list_tracks(song.id)
    assert [t.id for t in tracks] == [t1.id, t2.id]

    session = service.schedule_recording_session(
        song_id=song.id,
        band_id=1,
        studio="Studio A",
        start="2024-01-01T00:00",
        end="2024-01-01T02:00",
        cost_cents=5_000,
    )
    assert set(session.track_statuses.keys()) == {t1.id, t2.id}
