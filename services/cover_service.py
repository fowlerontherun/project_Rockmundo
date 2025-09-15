"""Service for handling song covers by other artists."""

from services.song_popularity_service import add_event
from services.song_service import SongService

song_service = SongService()


def record_cover(song_id: int, artist_id: int, revenue_cents: int = 0) -> None:
    """Record a cover performance or release and boost popularity.

    Alerts if the band does not have an active license for the song.
    """
    try:
        song_service.record_cover_usage(song_id, artist_id, revenue_cents)
    except PermissionError as exc:
        print(f"ALERT: {exc}")
        raise
    add_event(song_id, 5.0, f"cover:{artist_id}")
