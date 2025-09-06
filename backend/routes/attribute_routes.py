"""Routes for training user attributes."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.attribute_service import attribute_service

router = APIRouter()


class TrainAttributeRequest(BaseModel):
    stat: str
    amount: int


@router.post("/avatar/{user_id}/train_attribute")
def train_attribute(user_id: int, req: TrainAttributeRequest) -> dict:
    attr = attribute_service.train_attribute(user_id, req.stat, req.amount)
    return {"stat": attr.stat, "xp": attr.xp, "level": attr.level}
