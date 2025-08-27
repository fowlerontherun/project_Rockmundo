from __future__ import annotations

from typing import Dict

from models.quest import Quest, QuestReward


class QuestService:
    """Service for assigning quests and tracking player progress."""

    def __init__(self):
        # user_id -> {quest_id: current_stage_id}
        self.assignments: Dict[int, Dict[str, str]] = {}
        # user_id -> {quest_id: QuestReward}
        self.completed: Dict[int, Dict[str, QuestReward]] = {}

    def assign_quest(self, user_id: int, quest: Quest) -> None:
        """Assign a quest to a user starting at the initial stage."""
        self.assignments.setdefault(user_id, {})[quest.id] = quest.initial_stage

    def get_current_stage(self, user_id: int, quest: Quest):
        stage_id = self.assignments.get(user_id, {}).get(quest.id)
        if stage_id is None:
            return None
        return quest.get_stage(stage_id)

    def report_progress(self, user_id: int, quest: Quest, choice: str):
        """Advance the quest based on a branch choice and return the new stage."""
        current_stage_id = self.assignments.get(user_id, {}).get(quest.id)
        if current_stage_id is None:
            raise ValueError("Quest not assigned")
        current_stage = quest.get_stage(current_stage_id)
        if choice not in current_stage.branches:
            raise ValueError("Invalid branch choice")
        next_stage_id = current_stage.branches[choice]
        self.assignments[user_id][quest.id] = next_stage_id
        next_stage = quest.get_stage(next_stage_id)
        if next_stage.reward:
            self.completed.setdefault(user_id, {})[quest.id] = next_stage.reward
        return next_stage

    def claim_reward(self, user_id: int, quest_id: str):
        """Retrieve the reward for a completed quest stage if available."""
        return self.completed.get(user_id, {}).pop(quest_id, None)

    def resolve_outcome(self, user_id: int, quest: Quest):
        """Return the reward for the current stage without claiming it."""
        stage = self.get_current_stage(user_id, quest)
        return stage.reward if stage else None
