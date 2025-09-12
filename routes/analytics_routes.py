from fastapi import APIRouter

try:  # FastAPI stub in tests may not expose Depends
    from fastapi import Depends
except Exception:  # pragma: no cover - fallback for stubs
    def Depends(dependency):  # type: ignore
        return dependency

from backend.auth.dependencies import require_permission
from backend.models.analytics import (
    AggregatedMetrics,
    FanSegmentSummary,
    FanTrends,
)
from services.analytics_service import AnalyticsService
from services.fan_insight_service import FanInsightService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
svc = AnalyticsService()
fan_svc = FanInsightService()


@router.get("/time-series")
async def get_time_series(
    start_date: str,
    end_date: str,
    _: bool = Depends(require_permission(["admin"])),
) -> AggregatedMetrics:
    """Return aggregated metrics across domains for the given date range."""
    return svc.time_series(start_date, end_date)


@router.get("/fans/segments")
async def get_fan_segments(
    _: bool = Depends(require_permission(["admin"])),
) -> FanSegmentSummary:
    """Return fan demographic and engagement segment counts."""
    return fan_svc.segment_summary()


@router.get("/fans/trends")
async def get_fan_trends(
    start_date: str,
    end_date: str,
    _: bool = Depends(require_permission(["admin"])),
) -> FanTrends:
    """Return fan engagement trends over time."""
    return fan_svc.trends(start_date, end_date)
