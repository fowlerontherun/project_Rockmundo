from fastapi import APIRouter
from schemas.support_slot_schema import SupportSlotCreate, SupportSlotResponse
from models.support_slot import SupportSlot
from typing import List

router = APIRouter()
support_slots: List[SupportSlot] = []
slot_id_counter = 1

@router.post("/support_slots/", response_model=SupportSlotResponse)
def invite_support_band(data: SupportSlotCreate):
    global slot_id_counter
    slot = SupportSlot(
        id=slot_id_counter,
        main_band_id=data.main_band_id,
        support_band_id=data.support_band_id,
        tour_id=data.tour_id,
        fee=data.fee,
        status="invited"
    )
    support_slots.append(slot)
    slot_id_counter += 1
    return slot

@router.get("/support_slots/", response_model=List[SupportSlot])
def list_support_slots():
    return support_slots

@router.post("/support_slots/{slot_id}/respond")
def respond_to_invite(slot_id: int, accepted: bool):
    for slot in support_slots:
        if slot.id == slot_id:
            slot.status = "accepted" if accepted else "declined"
            return {"message": f"Support slot {'accepted' if accepted else 'declined'}."}
    return {"error": "Slot not found"}