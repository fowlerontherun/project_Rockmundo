from __future__ import annotations

from typing import Dict, List, Optional
import sqlite3


from models.tournament import Bracket, Match, Score
from backend.services import live_performance_service
from database import DB_PATH

class TournamentService:
    """Service for managing simple elimination tournaments."""

    def __init__(
        self,
        performance_service: Optional[object] = None,
        db_path: str = DB_PATH,
        prize_amount: int = 1000,
    ):
        # ``performance_service`` is expected to provide a ``simulate_gig``
        # function.  By default we use the module-level implementation from
        # :mod:`live_performance_service`.
        self.performance = performance_service or live_performance_service
        self.db_path = db_path
        self.prize_amount = prize_amount
        self.brackets: Dict[int, Bracket] = {}
        self._next_id = 1

    # Tournament management -------------------------------------------------
    def create_tournament(self, band_ids: List[int]) -> int:
        bracket = self._create_bracket(band_ids)
        tid = self._next_id
        self.brackets[tid] = bracket
        self._next_id += 1
        return tid

    def get_bracket(self, tournament_id: int) -> Optional[Bracket]:
        return self.brackets.get(tournament_id)

    # Core logic ------------------------------------------------------------
    def _create_bracket(self, band_ids: List[int]) -> Bracket:
        matches: List[Match] = []
        it = iter(band_ids)
        for b1, b2 in zip(it, it):
            matches.append(Match(b1, b2))
        bracket = Bracket()
        bracket.add_round(matches)
        return bracket

    def play_round(self, bracket: Bracket) -> Optional[int]:
        """Play the current round, returning champion id if concluded."""

        current = bracket.current_round()
        if not current:
            return None

        winners: List[int] = []
        for match in current:
            score1 = self._calculate_score(match.band1_id)
            score2 = self._calculate_score(match.band2_id)
            match.band1_score = score1.value
            match.band2_score = score2.value
            match.winner_id = match.band1_id if score1.value >= score2.value else match.band2_id
            winners.append(match.winner_id)
            self._award_prize(match.winner_id)

        if len(winners) == 1:
            # Champion determined
            return winners[0]

        next_round: List[Match] = []
        it = iter(winners)
        for b1, b2 in zip(it, it):
            next_round.append(Match(b1, b2))
        bracket.add_round(next_round)
        return None

    # Helpers ---------------------------------------------------------------
    def _calculate_score(self, band_id: int) -> Score:
        result = self.performance.simulate_gig(
            band_id=band_id,
            city="Arena City",
            venue="Grand Arena",
            setlist_revision_id=0,
        )
        return Score(
            band_id=band_id,
            fame_earned=result.get("fame_earned", 0),
            revenue_earned=result.get("revenue_earned", 0),
            crowd_size=result.get("crowd_size", 0),
        )

    def _award_prize(self, band_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "UPDATE bands SET revenue = COALESCE(revenue, 0) + ? WHERE id = ?",
            (self.prize_amount, band_id),
        )
        conn.commit()
        conn.close()
