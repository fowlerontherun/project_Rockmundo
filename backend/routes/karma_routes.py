from fastapi import APIRouter
from schemas.karma_schema import KarmaEventCreate
from models.karma import KarmaEvent
from datetime import datetime
from typing import List

router = APIRouter()
karma_events: List[KarmaEvent] = []
karma_id = 1

@router.post("/karma/", response_model=KarmaEvent)
def add_karma(event: KarmaEventCreate):
    global karma_id
    new_event = KarmaEvent(
        id=karma_id,
        user_id=event.user_id,
        score_change=event.score_change,
        reason=event.reason,
        auto=event.auto,
        visible_reason=event.visible_reason,
        timestamp=datetime.utcnow()
    )
    karma_events.append(new_event)
    karma_id += 1
    return new_event

@router.get("/karma/{user_id}", response_model=List[KarmaEvent])
def get_user_karma(user_id: int):
    return [k for k in karma_events if k.user_id == user_id]