# File: backend/routes/dashboard_routes.py
from typing import Optional

from backend.auth.dependencies import get_current_user_id, require_permission  # noqa: F401
from backend.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, HTTPException, Query, Request  # noqa: F401

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
svc = DashboardService()


@router.get("/summary")
async def dashboard_summary(
    user_id: int = Depends(get_current_user_id),
    band_id: Optional[int] = Query(None),
    top_n: int = Query(10, ge=1, le=50),
):
    try:
        return svc.summary(user_id=user_id, band_id=band_id, top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {e}")
