"""Service for onboarding questions and their effects."""

import random
from typing import Dict, List

from backend.models.onboarding import Question
from backend.seeds.question_seed import QUESTIONS


class OnboardingQuestionService:
    """Provide question sets and evaluate selected answers."""

    def get_questions(self, count: int = 3) -> List[Question]:
        """Return ``count`` random questions from the pool."""
        return random.sample(QUESTIONS, count)

    def evaluate_answers(self, answers: Dict[int, int]) -> tuple[int, Dict[str, int]]:
        """Calculate total XP and stat boosts for selected answers.

        Args:
            answers: mapping of ``question_id`` to ``option_index`` (0-based).

        Returns:
            A tuple ``(xp, boosts)`` where ``xp`` is the summed experience and
            ``boosts`` is a mapping of stat names to their cumulative boosts.
        """
        total_xp = 0
        boosts: Dict[str, int] = {}
        question_map = {q.id: q for q in QUESTIONS}
        for q_id, opt_index in answers.items():
            question = question_map.get(q_id)
            if not question or not 0 <= opt_index < len(question.options):
                continue
            option = question.options[opt_index]
            total_xp += option.xp
            boosts[option.stat] = boosts.get(option.stat, 0) + option.boost
        return total_xp, boosts


__all__ = ["OnboardingQuestionService"]
