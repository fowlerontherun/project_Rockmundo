from dataclasses import dataclass


@dataclass
class Workshop:
    """Admin-managed workshop event."""

    id: int | None
    skill_target: str
    xp_reward: int
    ticket_price: int
    schedule: str


__all__ = ["Workshop"]
