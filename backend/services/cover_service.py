"""Service for handling song covers by other artists."""

from backend.services.song_popularity_service import add_event


def record_cover(song_id: int, artist_id: int) -> None:
    """Record a cover performance or release and boost popularity."""
    add_event(song_id, 5.0, f"cover:{artist_id}")
