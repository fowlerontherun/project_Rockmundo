from __future__ import annotations

from typing import List

from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.skill_service import skill_service


def mix_tracks(performance_ids: List[int], user_id: int | None = None) -> List[int]:
    """Return identifiers for mixed audio tracks and award sound design XP.

    In the real application this function would take raw performance
    recordings and produce mixed tracks stored in an audio service.  For test
    purposes we simply return deterministic identifiers derived from the
    provided ``performance_ids``.

    If ``user_id`` is provided, sound-design XP is granted based on the
    number of performances mixed.
    """

    if user_id is not None:
        skill = Skill(
            id=SKILL_NAME_TO_ID["sound_design"],
            name="sound_design",
            category="creative",
        )
        skill_service.train(user_id, skill, 10 * len(performance_ids))

    # A simple deterministic transformation that is easy to assert in tests.
    return [pid + 1000 for pid in performance_ids]
