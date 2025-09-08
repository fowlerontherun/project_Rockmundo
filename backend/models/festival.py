from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class Festival(BaseModel):
    id: int
    name: str
    country: str
    location: str
    type: str  # 'major', 'medium', 'player'
    created_by: Optional[int]
    start_date: date
    end_date: date
    season: str
    stage_count: int
    max_capacity: int
    cost: float
    headliners: List[int]
    full_lineup: List[int]
    ticket_price: float
    attendance: int
    revenue: float
    genre_id: Optional[int]
    success_score: Optional[float]


class FestivalProposal(BaseModel):
    """Represents a player submitted festival idea awaiting votes."""

    id: int
    proposer_id: int
    name: str
    description: Optional[str] = None
    genre: str
    vote_count: int = 0
    approved: bool = False


class ProposalVote(BaseModel):
    """Record of a player's vote on a proposal."""

    proposal_id: int
    voter_id: int
