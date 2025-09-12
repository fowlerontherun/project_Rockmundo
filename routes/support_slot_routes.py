from __future__ import annotations

from datetime import datetime
from itertools import count
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

try:  # Authentication dependencies may not be available during tests
    from backend.auth.dependencies import get_current_user_id, require_permission
except Exception:  # pragma: no cover - fallback for docs builds
    def require_permission(_: List[str]):
        async def _noop() -> None:  # type: ignore[return-value]
            return None

        return _noop

    async def get_current_user_id() -> int:  # type: ignore[misc]
        return 0

# Router managing support slot scheduling
router = APIRouter(tags=["Support Slots"])

# simple in-memory storage for demonstration and testing purposes
_slots: dict[int, dict[str, object]] = {}
_id_seq = count(1)


class SupportSlotIn(BaseModel):
    """Payload for creating or updating a support slot."""

    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None


class SupportSlotOut(SupportSlotIn):
    id: int
    owner_id: int


@router.post(
    "",
    response_model=SupportSlotOut,
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def create_slot(
    payload: SupportSlotIn, user_id: int = Depends(get_current_user_id)
) -> SupportSlotOut:
    """Create a new support slot for the current user."""

    slot_id = next(_id_seq)
    slot = {"id": slot_id, "owner_id": user_id, **payload.model_dump()}
    _slots[slot_id] = slot
    return SupportSlotOut(**slot)


@router.get(
    "",
    response_model=List[SupportSlotOut],
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def list_slots() -> List[SupportSlotOut]:
    """Return all defined support slots."""

    return [SupportSlotOut(**slot) for slot in _slots.values()]


@router.get(
    "/{slot_id}",
    response_model=SupportSlotOut,
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def get_slot(slot_id: int) -> SupportSlotOut:
    """Retrieve a single support slot by identifier."""

    slot = _slots.get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return SupportSlotOut(**slot)


@router.put(
    "/{slot_id}",
    response_model=SupportSlotOut,
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def update_slot(
    slot_id: int,
    payload: SupportSlotIn,
    user_id: int = Depends(get_current_user_id),
) -> SupportSlotOut:
    """Update an existing support slot."""

    slot = _slots.get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    slot.update(payload.model_dump())
    _slots[slot_id] = slot
    return SupportSlotOut(**slot)


@router.delete(
    "/{slot_id}",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def delete_slot(slot_id: int) -> dict[str, bool]:
    """Delete a support slot."""

    if slot_id not in _slots:
        raise HTTPException(status_code=404, detail="Slot not found")
    del _slots[slot_id]
    return {"ok": True}

