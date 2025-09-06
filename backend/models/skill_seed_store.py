import json
from pathlib import Path
from typing import List

from backend.models.skill import Skill

# Path to the JSON file storing persisted skills
SKILL_SEED_PATH = Path(__file__).resolve().parent.parent / "database" / "skill_seed.json"


def load_skills() -> List[Skill]:
    """Load skills from the persisted JSON file.

    Returns an empty list if the file doesn't exist.
    """
    if SKILL_SEED_PATH.exists():
        data = json.loads(SKILL_SEED_PATH.read_text())
        skills: List[Skill] = []
        for item in data:
            prereqs = {int(k): v for k, v in item.get("prerequisites", {}).items()}
            prereqs = {
                int(k): v for k, v in item.get("prerequisites", {}).items()
            }
            item["prerequisites"] = prereqs
            skills.append(Skill(**item))
        return skills
    return []


def save_skills(skills: List[Skill]) -> None:
    """Persist the given skills to the JSON file."""
    SKILL_SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SKILL_SEED_PATH.open("w") as f:
        json.dump([s.__dict__ for s in skills], f, indent=2)
