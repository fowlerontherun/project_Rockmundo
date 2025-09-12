# File: backend/routes/music_routes.py
from fastapi import APIRouter, HTTPException
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_permission
from pydantic import BaseModel, Field
from typing import Optional

from services.music_service import MusicService
from services.music_metrics import MusicMetricsService

router = APIRouter(prefix="/music", tags=["Music"])
svc = MusicService()
metrics = MusicMetricsService()

class SaleIn(BaseModel):
    
item_id: int = Field(..., ge=1)
    quantity: int = Field(1, ge=1)
    revenue: float = Field(..., ge=0)
    is_vinyl: bool = False
    meta: Optional[str] = None

class StreamIn(BaseModel):
    
item_id: int = Field(..., ge=1)
    count: int = Field(1, ge=1)
    meta: Optional[str] = None

@router.post("/sales")
def record_sale(payload: SaleIn, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.record_sale(item_id=payload.item_id, quantity=payload.quantity, revenue=payload.revenue, is_vinyl=payload.is_vinyl, meta=payload.meta)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/streams")
def record_stream(payload: StreamIn, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.record_stream(item_id=payload.item_id, count=payload.count, meta=payload.meta)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics")
def get_metrics(user_id: int = Depends(get_current_user_id)):
    return metrics.totals()