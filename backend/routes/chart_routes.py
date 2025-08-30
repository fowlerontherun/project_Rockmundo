from backend.auth.dependencies import get_current_user_id
from backend.services.chart_service import ChartService
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter(prefix="/charts", tags=["Charts"])
chart_service = ChartService(db=None)


@router.get("/global/{week_start}")
def get_global_chart(
    week_start: str, _req: Request, user_id: int = Depends(get_current_user_id)
):
    return chart_service.get_chart("Global Top 100", week_start)


@router.post("/recalculate", status_code=204)
def recalculate_charts(
    _req: Request, user_id: int = Depends(get_current_user_id)
):
    try:
        chart_service.calculate_weekly_charts()
    except Exception as e:  # pragma: no cover - example stub
        raise HTTPException(status_code=500, detail=str(e))
