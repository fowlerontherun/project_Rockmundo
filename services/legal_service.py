from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol

from datetime import datetime

from backend.services.economy_service import EconomyService, EconomyError
from backend.services.karma_service import KarmaService
from models.legal import LegalCase, Filing, Verdict


class LegalService:
    """In-memory service managing legal disputes and registrations."""

    class CopyrightClient(Protocol):
        def register(self, song_id: int, lyrics: str) -> str: ...

    def __init__(
        self,
        economy: EconomyService,
        karma: KarmaService,
        copyright_client: Optional[CopyrightClient] = None,
    ) -> None:
        self.economy = economy
        self.karma = karma
        self.cases: Dict[int, LegalCase] = {}
        self._case_id = 1
        self._filing_id = 1
        self._verdict_id = 1
        self._copyright_client = copyright_client
        self.registrations: Dict[int, str] = {}

    # ---------------- case management ----------------
    def create_case(
        self, plaintiff_id: int, defendant_id: int, description: str, amount_cents: int = 0
    ) -> LegalCase:
        case = LegalCase(
            id=self._case_id,
            plaintiff_id=plaintiff_id,
            defendant_id=defendant_id,
        )
        filing = Filing(
            id=self._filing_id,
            case_id=case.id,
            filer_id=plaintiff_id,
            text=description,
            amount_cents=amount_cents,
        )
        case.filings.append(filing)
        self.cases[case.id] = case
        self._case_id += 1
        self._filing_id += 1
        return case

    def add_filing(self, case_id: int, filer_id: int, text: str) -> LegalCase:
        case = self.cases[case_id]
        filing = Filing(
            id=self._filing_id,
            case_id=case_id,
            filer_id=filer_id,
            text=text,
        )
        case.filings.append(filing)
        self._filing_id += 1
        return case

    def arbitrate_case(self, case_id: int, decision: str, penalty_cents: int = 0) -> LegalCase:
        case = self.cases[case_id]
        verdict = Verdict(
            id=self._verdict_id,
            case_id=case_id,
            decision=decision,
            penalty_cents=penalty_cents,
        )
        case.verdict = verdict
        case.status = "closed"
        self._verdict_id += 1

        if penalty_cents > 0:
            try:
                self.economy.transfer(case.defendant_id, case.plaintiff_id, penalty_cents)
            except EconomyError:
                # if funds insufficient, just ignore for minimal implementation
                pass
            # apply negative karma to defendant proportional to penalty
            self.karma.adjust_karma(
                case.defendant_id,
                -penalty_cents,
                reason="legal_penalty",
                source="legal",
            )
        return case

    def get_case(self, case_id: int) -> Optional[LegalCase]:
        return self.cases.get(case_id)

    # ---------------- copyright registration ----------------
    def register_copyright(self, song_id: int, lyrics: str) -> Optional[str]:
        """Register song lyrics with an external copyright service."""

        if not self._copyright_client:
            return None
        registration_id = self._copyright_client.register(song_id, lyrics)
        self.registrations[song_id] = registration_id
        return registration_id
