
from datetime import datetime
from typing import Optional


class RandomEvent:
    """Simple data holder for random event records.

    The model stores structured impact fields instead of a single text string
    so services can apply outcomes directly to game state.
    """

    def __init__(
        self,
        id,
        band_id: Optional[int] = None,
        avatar_id: Optional[int] = None,
        type: str = "",
        description: str = "",
        fame: int = 0,
        funds: int = 0,
        skill: Optional[str] = None,
        skill_delta: int = 0,
        triggered_at: Optional[str] = None,
    ):
        self.id = id
        self.band_id = band_id
        self.avatar_id = avatar_id
        self.type = type  # e.g., 'delay', 'press', 'fan_interaction'
        self.description = description
        # numeric impact fields
        self.fame = fame
        self.funds = funds
        self.skill = skill
        self.skill_delta = skill_delta
        self.triggered_at = triggered_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
