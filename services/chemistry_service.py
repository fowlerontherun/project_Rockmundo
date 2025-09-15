"""Service for managing player chemistry scores."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from models.player_chemistry import Base, PlayerChemistry

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "rockmundo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)


class ChemistryService:
    """Handles initialization and adjustment of player chemistry."""

    def __init__(
        self, session_factory: Callable[[], Session] | sessionmaker = SessionLocal
    ) -> None:
        self.session_factory = session_factory
        try:
            Base.metadata.create_all(bind=self.session_factory().get_bind())
        except SQLAlchemyError:
            logger.exception("Failed to initialize ChemistryService database")
            raise

    @staticmethod
    def _normalize(a_id: int, b_id: int) -> tuple[int, int]:
        return (a_id, b_id) if a_id <= b_id else (b_id, a_id)

    def initialize_pair(self, a_id: int, b_id: int) -> PlayerChemistry:
        """Create a chemistry record if one does not already exist."""

        a_id, b_id = self._normalize(a_id, b_id)
        with self.session_factory() as session:
            with session.begin():
                pair = (
                    session.query(PlayerChemistry)
                    .filter_by(player_a_id=a_id, player_b_id=b_id)
                    .first()
                )
                if pair:
                    return pair

                score = 50
                roll = random.random()
                if roll < 0.05:
                    score = random.randint(81, 100)
                elif roll > 0.95:
                    score = random.randint(0, 19)

                pair = PlayerChemistry(
                    player_a_id=a_id, player_b_id=b_id, score=score
                )
                session.add(pair)
            session.refresh(pair)
            return pair

    def adjust_pair(self, a_id: int, b_id: int, delta: int) -> PlayerChemistry:
        """Modify chemistry score by ``delta`` for the given pair."""

        a_id, b_id = self._normalize(a_id, b_id)
        with self.session_factory() as session:
            with session.begin():
                pair = (
                    session.query(PlayerChemistry)
                    .filter_by(player_a_id=a_id, player_b_id=b_id)
                    .first()
                )
                if not pair:
                    pair = PlayerChemistry(
                        player_a_id=a_id, player_b_id=b_id, score=50
                    )
                    session.add(pair)
                pair.score += delta
                pair.last_updated = func.now()
            session.refresh(pair)
            return pair

    def list_for_player(self, player_id: int) -> list[PlayerChemistry]:
        """Return all chemistry records involving ``player_id``."""

        with self.session_factory() as session:
            return (
                session.query(PlayerChemistry)
                .filter(
                    (PlayerChemistry.player_a_id == player_id)
                    | (PlayerChemistry.player_b_id == player_id)
                )
                .all()
            )
