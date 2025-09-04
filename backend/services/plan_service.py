"""High-level planning for daily schedules.

This module maps high level category selections (social, career, band)
into concrete activity names and fills the remaining day with rest
activities.  The service is intentionally simple and in-memory so it can
be used by routes and tests without any external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from backend.services.skill_service import skill_service

# Default mapping of category -> list of activity names.
CATEGORY_MAP: Dict[str, List[str]] = {
    "social": ["network", "promote"],
    "career": ["practice", "songwriting"],
    "band": ["rehearsal", "gig_prep"],
}

# Number of slots that make up a day in the generated plan.
DEFAULT_SLOTS = 8


@dataclass
class PlanService:
    """Generate simple daily plans based on category selections."""

    # expose defaults for easy access in tests or other modules
    CATEGORY_MAP = CATEGORY_MAP
    DEFAULT_SLOTS = DEFAULT_SLOTS

    category_map: Dict[str, List[str]] = field(default_factory=lambda: CATEGORY_MAP)
    slots: int = DEFAULT_SLOTS

    def create_plan(
        self,
        *,
        social_pct: int = 0,
        career_pct: int = 0,
        band_pct: int = 0,
    ) -> List[str]:
        """Return a list of activities for the day.

        The ``*_pct`` arguments describe the percentage of the day that
        should be devoted to each category.  Percentages are converted to
        slot counts based on ``slots`` and any remaining slots are filled
        with ``"rest"`` activities.
        """

        schedule: List[str] = []
        allocations = {
            "social": social_pct,
            "career": career_pct,
            "band": band_pct,
        }

        for category, pct in allocations.items():
            if pct <= 0:
                continue
            activities = self.category_map.get(category, [])
            if not activities:
                continue
            count = int(self.slots * (pct / 100))
            for i in range(count):
                schedule.append(activities[i % len(activities)])

        while len(schedule) < self.slots:
            schedule.append("rest")

        return schedule[: self.slots]

    def recommend_activities(self, user_id: int, goals: List[str]) -> List[str]:
        """Recommend activities based on the user's skill levels.

        For each goal (a skill name) the user's current level is inspected
        using :mod:`backend.services.skill_service`.  Low level skills
        receive "practice" recommendations while higher level skills are
        encouraged with "perform" suggestions.
        """

        suggestions: List[str] = []
        for goal in goals:
            skill = None
            for (uid, _), s in skill_service._skills.items():
                if uid == user_id and s.name == goal:
                    skill = s
                    break
            level = skill.level if skill else 1
            if level < 5:
                suggestions.append(f"practice {goal}")
            else:
                suggestions.append(f"perform {goal}")
        return suggestions


plan_service = PlanService()

__all__ = ["PlanService", "plan_service"]
