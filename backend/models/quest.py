from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class QuestReward(BaseModel):
    """Represents a reward granted for completing a quest stage."""

    type: str
    amount: int


class QuestStage(BaseModel):
    """A single stage within a quest.

    Each stage can branch into other stages depending on the player's
    choice and may optionally grant a reward when reached.
    """

    id: str
    description: str
    branches: Dict[str, str] = {}
    reward: Optional[QuestReward] = None


class Quest(BaseModel):
    """Definition of a quest with multiple stages and branching paths."""

    id: str
    name: str
    stages: Dict[str, QuestStage]
    initial_stage: str

    def get_stage(self, stage_id: str) -> QuestStage:
        return self.stages[stage_id]
