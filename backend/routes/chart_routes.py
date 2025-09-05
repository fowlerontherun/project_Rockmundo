from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id
from backend.services.chart_service import calculate_weekly_chart, get_chart

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/{region}/{week_start}")
def get_global_chart(
    region: str,
    week_start: str,
    _req: Request,
    user_id: int = Depends(get_current_user_id),
):
    return get_chart("Global Top 100", region, week_start)


@router.post("/{region}/recalculate", status_code=204)
def recalculate_charts(
    region: str, _req: Request, user_id: int = Depends(get_current_user_id)
):
    try:
        calculate_weekly_chart(region=region)
    except Exception as e:  # pragma: no cover - example stub
        raise HTTPException(status_code=500, detail=str(e))
