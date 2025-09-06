"""Seed data for default skills."""

from backend.models.skill import Skill

# name, category, parent_name, prerequisites_by_name
_RAW_SKILLS: list[tuple[str, str, str | None, dict[str, int]]] = [
    ("guitar", "instrument", None, {}),
    ("bass", "instrument", None, {}),
    ("vocals", "performance", None, {}),
    ("songwriting", "creative", None, {}),
    ("performance", "stage", None, {}),
    # Expanded instrument skills
    ("drums", "instrument", None, {}),
    ("keyboard", "instrument", None, {}),
    ("piano", "instrument", "keyboard", {"keyboard": 100}),
    ("violin", "instrument", None, {}),
    ("saxophone", "instrument", None, {}),
    ("trumpet", "instrument", None, {}),
    ("dj", "instrument", None, {}),
    ("turntablism", "instrument", "dj", {"dj": 100}),
    # Expanded performance skills
    ("dance", "performance", None, {}),
    ("stage_presence", "performance", None, {}),
    ("crowd_interaction", "performance", None, {}),
    ("pyrotechnics", "performance", None, {}),
    ("live_streaming", "performance", None, {}),
    # Expanded creative skills
    ("composition", "creative", None, {}),
    ("arrangement", "creative", None, {}),
    ("music_production", "creative", None, {}),
    ("mixing", "creative", "music_production", {"music_production": 100}),
    ("mastering", "creative", "music_production", {"music_production": 100}),
    ("music_theory", "creative", None, {}),
    ("ear_training", "creative", None, {}),
    # Image and style skills
    ("fashion", "image", None, {}),
    ("image_management", "image", None, {}),
    # Business skills
    ("marketing", "business", None, {}),
    ("public_relations", "business", None, {}),
    ("financial_management", "business", None, {}),
    ("social_media_management", "business", None, {}),
]


def _build_skills() -> list[Skill]:
    skills: list[Skill] = []
    name_to_id: dict[str, int] = {}
    for idx, (name, category, parent, prereq_names) in enumerate(
        _RAW_SKILLS, start=1
    ):
        parent_id = name_to_id.get(parent)
        prereqs = {
            name_to_id[pname]: level
            for pname, level in prereq_names.items()
            if pname in name_to_id
        }
        skill = Skill(
            id=idx,
            name=name,
            category=category,
            parent_id=parent_id,
            prerequisites=prereqs,
        )
        skills.append(skill)
        name_to_id[name] = idx
    return skills


SEED_SKILLS = _build_skills()
SKILL_NAME_TO_ID = {skill.name: skill.id for skill in SEED_SKILLS}


def get_seed_skills() -> list[Skill]:
    """Return the list of default skills."""
    return SEED_SKILLS


__all__ = ["get_seed_skills", "SEED_SKILLS", "SKILL_NAME_TO_ID"]
