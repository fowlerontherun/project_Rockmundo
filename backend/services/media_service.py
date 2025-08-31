"""Media placement service for film/TV and other exposure channels."""

from backend.services.song_popularity_service import add_event


def record_media_placement(song_id: int, placement_type: str) -> None:
    """Record that a song was placed in some media and boost its popularity.

    Args:
        song_id: The song receiving placement.
        placement_type: e.g. "film", "tv", "ad".
    """
    boost = 20.0 if placement_type.lower() == "film" else 10.0
    add_event(song_id, boost, placement_type)
