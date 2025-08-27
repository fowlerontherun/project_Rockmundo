from fastapi import APIRouter

try:  # FastAPI stub in tests may not expose Depends
    from fastapi import Depends
except Exception:  # pragma: no cover - fallback for stubs
    def Depends(dependency):  # type: ignore
        return dependency

from auth.dependencies import require_role
from services.analytics_service import AnalyticsService
from models.analytics import AggregatedMetrics

router = APIRouter(prefix="/analytics", tags=["Analytics"])
svc = AnalyticsService()


@router.get("/time-series")
async def get_time_series(
    start_date: str,
    end_date: str,
    _: bool = Depends(require_role(["admin"])),
) -> AggregatedMetrics:
    """Return aggregated metrics across domains for the given date range."""
    return svc.time_series(start_date, end_date)
