# File: backend/routes/admin_analytics_routes.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from services.analytics_service import AnalyticsService

# Auth middleware / role dependency hook
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])
svc = AnalyticsService()

@router.get("/kpis", dependencies=[Depends(require_role(["admin","moderator"]))])
def kpis(period_start: str, period_end: str):
    """KPIs for streams, digital, vinyl, and tickets between [period_start, period_end]."""
    try:
        return svc.kpis(period_start, period_end)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-songs", dependencies=[Depends(require_role(["admin","moderator"]))])
def top_songs(period_start: str, period_end: str, limit: int = 20):
    """Top songs by streams and by digital revenue."""
    try:
        return svc.top_songs(period_start, period_end, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-albums", dependencies=[Depends(require_role(["admin","moderator"]))])
def top_albums(period_start: str, period_end: str, limit: int = 20):
    """Top albums by digital revenue and by vinyl revenue."""
    try:
        return svc.top_albums(period_start, period_end, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/royalty-runs/recent", dependencies=[Depends(require_role(["admin","moderator"]))])
def recent_royalty_runs(limit: int = 20):
    """Recent royalty runs."""
    try:
        return svc.recent_royalty_runs(limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/royalties/by-band", dependencies=[Depends(require_role(["admin","moderator"]))])
def royalties_by_band(run_id: int):
    """Sum of royalty amounts by band for a specific run."""
    try:
        return svc.royalties_summary_by_band(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))