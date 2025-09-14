from __future__ import annotations

from typing import Dict

from backend.models.quest import Quest, QuestReward, QuestStage
from services.city_service import city_service
from services.quest_admin_service import QuestAdminService
from services.xp_event_service import XPEventService


class QuestService:
    """Service for assigning quests and tracking player progress."""

    def __init__(self):
        # user_id -> {quest_id: current_stage_id}
        self.assignments: Dict[int, Dict[str, str]] = {}
        # user_id -> {quest_id: QuestReward}
        self.completed: Dict[int, Dict[str, QuestReward]] = {}
        self.admin_service = QuestAdminService()
        self.xp_events = XPEventService()

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
        reward = self.completed.get(user_id, {}).pop(quest_id, None)
        if reward and reward.type == "xp":
            mult = self.xp_events.get_active_multiplier()
            reward = QuestReward(type="xp", amount=int(reward.amount * mult))
        return reward

    def resolve_outcome(self, user_id: int, quest: Quest):
        """Return the reward for the current stage without claiming it."""
        stage = self.get_current_stage(user_id, quest)
        return stage.reward if stage else None

    def load_quest(self, quest_id: int) -> Quest:
        """Load a quest definition from the database."""
        data = self.admin_service.get_quest(quest_id)
        if not data:
            raise ValueError("Quest not found")
        stages = {}
        for st in data["stages"].values():
            reward = QuestReward(**st["reward"]) if st.get("reward") else None
            stages[st["id"]] = QuestStage(
                id=st["id"],
                description=st["description"],
                branches=st.get("branches", {}),
                reward=reward,
            )
        return Quest(
            id=str(data["id"]),
            name=data["name"],
            stages=stages,
            initial_stage=data["initial_stage"],
        )

    # --------- city influenced quests ---------
    def generate_city_quest(self, city_name: str) -> Quest:
        """Create a simple quest themed around the city's popular style."""
        city = city_service.get_city(city_name)
        if not city:
            raise ValueError("Unknown city")
        style = city.popular_style()
        reward = QuestReward(type="fame", amount=max(1, city.population // 100_000))
        stage = QuestStage(id="start", description=f"Perform a {style} show in {city_name}", branches={}, reward=reward)
        return Quest(id=f"{city_name}_{style}", name=f"{city_name} {style} Craze", stages={"start": stage}, initial_stage="start")
