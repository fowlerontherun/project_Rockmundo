"""Seed data for random in-game events."""

from seeds.quest_data import get_seed_quests
from seeds.skill_seed import SKILL_NAME_TO_ID

QUESTS = {quest.id: quest for quest in get_seed_quests()}


def get_seed_events():
    """Return a list of random events, some tied to quests."""
    return [
        {
            "name": "Sprained Wrist",
            "type": "injury",
            "effect_type": "block_skill",
            "skill_id": SKILL_NAME_TO_ID["guitar"],
            "duration_days": 5,
            "trigger_chance": 0.01,
            "related_quest": QUESTS["first_gig"].id,
        },
        {
            "name": "Lost Love for Guitar",
            "type": "burnout",
            "effect_type": "freeze_progress",
            "skill_id": SKILL_NAME_TO_ID["guitar"],
            "duration_days": 3,
            "trigger_chance": 0.01,
        },
        {
            "name": "Throat Infection",
            "type": "illness",
            "effect_type": "block_skill",
            "skill_id": SKILL_NAME_TO_ID["vocals"],
            "duration_days": 4,
            "trigger_chance": 0.01,
        },
        {
            "name": "Emotional Slump",
            "type": "emotional",
            "effect_type": "decay_skill",
            "skill_id": SKILL_NAME_TO_ID["songwriting"],
            "duration_days": 2,
            "trigger_chance": 0.01,
        },
    ]
