"""Seed data for music genres and subgenres."""

from typing import List, Dict, Optional


def get_seed_genres() -> List[Dict[str, Optional[int]]]:
    """Return a list of genres with optional parent genre IDs."""
    return [
        {"id": 1, "name": "Rock", "parent_id": None},
        {"id": 2, "name": "Pop", "parent_id": None},
        {"id": 3, "name": "Jazz", "parent_id": None},
        {"id": 4, "name": "Hip Hop", "parent_id": None},
        {"id": 5, "name": "Electronic", "parent_id": None},
        {"id": 6, "name": "Hard Rock", "parent_id": 1},
        {"id": 7, "name": "Alternative Rock", "parent_id": 1},
        {"id": 8, "name": "Synth Pop", "parent_id": 2},
        {"id": 9, "name": "K-Pop", "parent_id": 2},
        {"id": 10, "name": "Smooth Jazz", "parent_id": 3},
        {"id": 11, "name": "Bebop", "parent_id": 3},
        {"id": 12, "name": "Trap", "parent_id": 4},
        {"id": 13, "name": "Boom Bap", "parent_id": 4},
        {"id": 14, "name": "House", "parent_id": 5},
        {"id": 15, "name": "Techno", "parent_id": 5},
    ]
