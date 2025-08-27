# File: backend/routes/admin_analytics_routes.py
from fastapi import APIRouter, HTTPException, Request
from auth.dependencies import get_current_user_id, require_role
from services.analytics_service import AnalyticsService
from services.admin_service import AdminService

# Auth middleware / role dependency hook
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/analytics", tags=["Admin Analytics"])
svc = AnalyticsService()


class _AdminDB:
    """Minimal stand‑in used for audit logging during tests."""

    def insert_admin_action(self, action):
        pass


admin_logger = AdminService(_AdminDB())

@router.get("/kpis")
async def kpis(req: Request, period_start: str, period_end: str):
    """KPIs for streams, digital, vinyl, and tickets between [period_start, period_end]."""
    try:
        admin_id = await get_current_user_id(req)
        await require_role(["admin", "moderator"], admin_id)
        result = svc.kpis(period_start, period_end)
        admin_logger.log_action(
            admin_id,
            "analytics_kpis",
            {"period_start": period_start, "period_end": period_end},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-songs")
async def top_songs(
    req: Request,
    period_start: str,
    period_end: str,
    limit: int = 20,
):
    """Top songs by streams and by digital revenue."""
    try:
        admin_id = await get_current_user_id(req)
        await require_role(["admin", "moderator"], admin_id)
        result = svc.top_songs(period_start, period_end, limit)
        admin_logger.log_action(
            admin_id,
            "analytics_top_songs",
            {
                "period_start": period_start,
                "period_end": period_end,
                "limit": limit,
            },
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-albums")
async def top_albums(
    req: Request,
    period_start: str,
    period_end: str,
    limit: int = 20,
):
    """Top albums by digital revenue and by vinyl revenue."""
    try:
        admin_id = await get_current_user_id(req)
        await require_role(["admin", "moderator"], admin_id)
        result = svc.top_albums(period_start, period_end, limit)
        admin_logger.log_action(
            admin_id,
            "analytics_top_albums",
            {
                "period_start": period_start,
                "period_end": period_end,
                "limit": limit,
            },
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/royalty-runs/recent")
async def recent_royalty_runs(req: Request, limit: int = 20):
    """Recent royalty runs."""
    try:
        admin_id = await get_current_user_id(req)
        await require_role(["admin", "moderator"], admin_id)
        result = svc.recent_royalty_runs(limit)
        admin_logger.log_action(
            admin_id,
            "analytics_recent_royalty_runs",
            {"limit": limit},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/royalties/by-band")
async def royalties_by_band(req: Request, run_id: int):
    """Sum of royalty amounts by band for a specific run."""
    try:
        admin_id = await get_current_user_id(req)
        await require_role(["admin", "moderator"], admin_id)
        result = svc.royalties_summary_by_band(run_id)
        admin_logger.log_action(
            admin_id,
            "analytics_royalties_by_band",
            {"run_id": run_id},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))