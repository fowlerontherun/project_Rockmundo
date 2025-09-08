import sys
from pathlib import Path
# ruff: noqa: I001

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from backend.services.festival_proposal_service import (  # noqa: E402
    FestivalProposalService,
    ProposalIn,
)


def _setup(tmp_path: Path) -> FestivalProposalService:
    db = tmp_path / "festival.sqlite"
    svc = FestivalProposalService(db_path=db)
    svc.ensure_schema()
    return svc


def test_approval_and_trends(tmp_path: Path) -> None:
    svc = _setup(tmp_path)
    pid1 = svc.submit_proposal(
        ProposalIn(proposer_id=1, name="Rock Fest", description=None, genre="rock")
    )
    pid2 = svc.submit_proposal(
        ProposalIn(proposer_id=2, name="Jazz Fest", description=None, genre="jazz")
    )
    svc.vote(pid1)
    svc.vote(pid1)
    svc.vote(pid2)

    svc.approve(pid1)
    p1 = svc.get(pid1)
    assert p1["approved"] == 1

    trends = svc.genre_trends()
    assert trends == {"rock": 2, "jazz": 1}
