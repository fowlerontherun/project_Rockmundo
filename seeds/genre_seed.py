

"""Seed data for music genres with demographic preferences."""

from models.genre import Genre

SEED_GENRES = [
    Genre(
        id=1,
        name="Rock",
        subgenres=["Hard Rock", "Indie Rock", "Punk Rock"],
        popularity={
            "age": {"teen": 0.6, "young_adult": 0.8, "adult": 0.7},
            "countries": {"US": 0.8, "UK": 0.7, "JP": 0.5},
            "genders": {"male": 0.7, "female": 0.6, "nonbinary": 0.6},
            "orientations": {"hetero": 0.7, "lgbtq": 0.8},
        },
    ),
    Genre(
        id=2,
        name="Pop",
        subgenres=["Electropop", "Teen Pop", "Dance Pop"],
        popularity={
            "age": {"teen": 0.9, "young_adult": 0.8, "adult": 0.7},
            "countries": {"US": 0.9, "BR": 0.8, "JP": 0.9},
            "genders": {"male": 0.8, "female": 0.9, "nonbinary": 0.8},
            "orientations": {"hetero": 0.85, "lgbtq": 0.9},
        },
    ),
    Genre(
        id=3,
        name="Jazz",
        subgenres=["Smooth Jazz", "Bebop"],
        popularity={
            "age": {"teen": 0.3, "young_adult": 0.5, "adult": 0.8, "senior": 0.9},
            "countries": {"US": 0.6, "FR": 0.7, "JP": 0.5},
            "genders": {"male": 0.6, "female": 0.6, "nonbinary": 0.6},
            "orientations": {"hetero": 0.6, "lgbtq": 0.7},
        },
    ),
    Genre(
        id=4,
        name="Electronic",
        subgenres=["EDM", "House", "Techno"],
        popularity={
            "age": {"teen": 0.7, "young_adult": 0.9, "adult": 0.6},
            "countries": {"DE": 0.8, "US": 0.7, "UK": 0.7},
            "genders": {"male": 0.7, "female": 0.7, "nonbinary": 0.8},
            "orientations": {"hetero": 0.7, "lgbtq": 0.85},
        },
    ),
]

GENRE_NAME_TO_ID = {genre.name: genre.id for genre in SEED_GENRES}


def get_seed_genres() -> list[Genre]:
    """Return the list of default genres."""
    return SEED_GENRES


__all__ = ["get_seed_genres", "SEED_GENRES", "GENRE_NAME_TO_ID"]

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

