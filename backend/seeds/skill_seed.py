"""Seed data for default skills."""

from backend.models.skill import Skill

SEED_SKILLS = [
    Skill(id=1, name="guitar", category="instrument"),
    Skill(id=2, name="bass", category="instrument"),
    Skill(id=3, name="vocals", category="performance"),
    Skill(id=4, name="songwriting", category="creative"),
    Skill(id=5, name="performance", category="stage"),
    # Expanded instrument skills
    Skill(id=6, name="drums", category="instrument"),
    Skill(id=7, name="keyboard", category="instrument"),
    Skill(id=8, name="piano", category="instrument", parent_id=7),
    Skill(id=9, name="violin", category="instrument"),
    Skill(id=10, name="saxophone", category="instrument"),
    Skill(id=11, name="trumpet", category="instrument"),
    Skill(id=12, name="dj", category="instrument"),
    Skill(id=13, name="turntablism", category="instrument", parent_id=12),
    # Expanded performance skills
    Skill(id=14, name="dance", category="performance"),
    Skill(id=15, name="stage_presence", category="performance"),
    Skill(id=16, name="crowd_interaction", category="performance"),
    Skill(id=17, name="pyrotechnics", category="performance"),
    # Expanded creative skills
    Skill(id=18, name="composition", category="creative"),
    Skill(id=19, name="arrangement", category="creative"),
    Skill(id=20, name="music_production", category="creative"),
    Skill(id=21, name="mixing", category="creative", parent_id=20),
    Skill(id=22, name="mastering", category="creative", parent_id=20),
    Skill(id=23, name="music_theory", category="creative"),
    Skill(id=24, name="ear_training", category="creative"),
    # Image and style skills
    Skill(id=25, name="fashion", category="image"),
    Skill(id=26, name="image_management", category="image"),
    # Business skills
    Skill(id=27, name="marketing", category="business"),
    Skill(id=28, name="public_relations", category="business"),
    Skill(id=29, name="financial_management", category="business"),
]

SKILL_NAME_TO_ID = {skill.name: skill.id for skill in SEED_SKILLS}


def get_seed_skills() -> list[Skill]:
    """Return the list of default skills."""
    return SEED_SKILLS


__all__ = ["get_seed_skills", "SEED_SKILLS", "SKILL_NAME_TO_ID"]
