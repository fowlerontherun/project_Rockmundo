import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


def _row_to_dict(row: sqlite3.Row) -> Dict[str, object]:
    return {k: row[k] for k in row.keys()}


@dataclass
class ProposalIn:
    proposer_id: int
    name: str
    description: Optional[str]
    genre: str


class FestivalProposalService:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS festival_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposer_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    genre TEXT,
                    vote_count INTEGER NOT NULL DEFAULT 0,
                    approved INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def submit_proposal(self, data: ProposalIn) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO festival_proposals (proposer_id, name, description, genre)
                VALUES (?, ?, ?, ?)
                """,
                (data.proposer_id, data.name, data.description, data.genre),
            )
            conn.commit()
            return int(cur.lastrowid)

    def vote(self, proposal_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE festival_proposals SET vote_count = vote_count + 1 WHERE id = ?",
                (proposal_id,),
            )
            conn.commit()
            cur.execute(
                "SELECT vote_count FROM festival_proposals WHERE id = ?",
                (proposal_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def approve(self, proposal_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE festival_proposals SET approved = 1 WHERE id = ?",
                (proposal_id,),
            )
            conn.commit()

    def get(self, proposal_id: int) -> Optional[Dict[str, object]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM festival_proposals WHERE id = ?",
                (proposal_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row) if row else None

    def genre_trends(self) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT genre, SUM(vote_count) FROM festival_proposals GROUP BY genre"
            )
            return {genre: int(count) for genre, count in cur.fetchall()}
