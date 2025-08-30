"""Seed data for default skills."""

from backend.models.skill import Skill

SEED_SKILLS = [
    Skill(id=1, name="guitar", category="instrument"),
    Skill(id=2, name="bass", category="instrument"),
    Skill(id=3, name="vocals", category="performance"),
    Skill(id=4, name="songwriting", category="creative"),
    Skill(id=5, name="performance", category="stage"),
]

SKILL_NAME_TO_ID = {skill.name: skill.id for skill in SEED_SKILLS}


def get_seed_skills() -> list[Skill]:
    """Return the list of default skills."""
    return SEED_SKILLS


__all__ = ["get_seed_skills", "SEED_SKILLS", "SKILL_NAME_TO_ID"]
