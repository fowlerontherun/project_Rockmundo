from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic models used by the gameplay services and tests. These remain the
# same so existing quest logic continues to work. They represent an in-memory
# quest definition.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Dataclasses that map directly to the persisted quest schema.  The admin
# service uses these when reading/writing from the SQLite database.
# ---------------------------------------------------------------------------


@dataclass
class QuestDB:
    id: Optional[int]
    name: str
    version: int
    initial_stage: str


@dataclass
class QuestStageDB:
    id: Optional[int]
    quest_id: int
    stage_id: str
    description: str
    reward_type: Optional[str] = None
    reward_amount: Optional[int] = None


@dataclass
class QuestBranchDB:
    id: Optional[int]
    stage_id: int
    choice: str
    next_stage_id: str
