from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from backend.auth.dependencies import get_current_user_id, require_permission
except Exception:  # pragma: no cover
    def require_permission(_: list[str]):
        async def _noop() -> None:  # type: ignore[return-value]
            return None
        return _noop

    async def get_current_user_id() -> int:  # type: ignore[misc]
        return 0

from services.festival_proposal_service import FestivalProposalService, ProposalIn

router = APIRouter(prefix="/festival/proposals", tags=["Festival Proposals"])
svc = FestivalProposalService()
svc.ensure_schema()


class ProposalCreate(BaseModel):
    name: str
    description: str | None = None
    genre: str


@router.post("")
async def submit_proposal(
    payload: ProposalCreate, user_id: int = Depends(get_current_user_id)
) -> dict:
    pid = svc.submit_proposal(
        ProposalIn(
            proposer_id=user_id,
            name=payload.name,
            description=payload.description,
            genre=payload.genre,
        )
    )
    return {"proposal_id": pid}


@router.post("/{proposal_id}/vote")
async def vote(
    proposal_id: int, user_id: int = Depends(get_current_user_id)
) -> dict:
    votes = svc.vote(proposal_id, user_id)
    return {"votes": votes}


@router.post(
    "/{proposal_id}/approve",
    dependencies=[Depends(require_permission(["admin"]))],
)
async def approve(proposal_id: int) -> dict:
    svc.approve(proposal_id)
    return {"status": "approved"}


@router.get("/trends/genres")
async def genre_trends() -> dict:
    return svc.genre_trends()
