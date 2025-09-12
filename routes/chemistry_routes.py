from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.chemistry_service import ChemistryService

router = APIRouter(prefix="/chemistry", tags=["chemistry"])
svc = ChemistryService()


class Adjustment(BaseModel):
    delta: int = 1


@router.get("/{player_id}")
def list_chemistry(player_id: int, _uid: int = Depends(get_current_user_id)):
    pairs = svc.list_for_player(player_id)
    return [
        {"player_a_id": p.player_a_id, "player_b_id": p.player_b_id, "score": p.score}
        for p in pairs
    ]


@router.post(
    "/{player_a_id}/{player_b_id}/adjust",
    dependencies=[Depends(require_permission(["admin"]))],
)
def adjust_pair(
    player_a_id: int,
    player_b_id: int,
    payload: Adjustment,
    _uid: int = Depends(get_current_user_id),
):
    pair = svc.adjust_pair(player_a_id, player_b_id, payload.delta)
    return {"player_a_id": pair.player_a_id, "player_b_id": pair.player_b_id, "score": pair.score}
