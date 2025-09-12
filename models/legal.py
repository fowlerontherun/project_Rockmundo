from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Filing:
    """Represents a filing or statement made in a case."""

    id: int
    case_id: int
    filer_id: int
    text: str
    amount_cents: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Verdict:
    """Outcome of a legal case."""

    id: int
    case_id: int
    decision: str
    penalty_cents: int = 0
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LegalCase:
    """Represents a dispute between two parties."""

    id: int
    plaintiff_id: int
    defendant_id: int
    status: str = "open"
    filings: List[Filing] = field(default_factory=list)
    verdict: Optional[Verdict] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plaintiff_id": self.plaintiff_id,
            "defendant_id": self.defendant_id,
            "status": self.status,
            "filings": [f.__dict__ for f in self.filings],
            "verdict": self.verdict.__dict__ if self.verdict else None,
        }
