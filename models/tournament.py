from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Score:
    """Represents performance metrics for a band within a match."""

    band_id: int
    fame_earned: int = 0
    revenue_earned: int = 0
    crowd_size: int = 0

    @property
    def value(self) -> int:
        """Total points used to determine winners.

        Currently this simply uses fame earned from a performance but can be
        extended with other metrics.
        """

        return self.fame_earned


@dataclass
class Match:
    """A single contest between two bands."""

    band1_id: int
    band2_id: int
    band1_score: Optional[int] = None
    band2_score: Optional[int] = None
    winner_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "band1_id": self.band1_id,
            "band2_id": self.band2_id,
            "band1_score": self.band1_score,
            "band2_score": self.band2_score,
            "winner_id": self.winner_id,
        }


@dataclass
class Bracket:
    """A collection of rounds, each round containing matches."""

    rounds: List[List[Match]] = field(default_factory=list)

    def add_round(self, matches: List[Match]) -> None:
        self.rounds.append(matches)

    def current_round(self) -> List[Match]:
        return self.rounds[-1] if self.rounds else []

    def to_dict(self) -> dict:
        return {"rounds": [[m.to_dict() for m in rnd] for rnd in self.rounds]}
