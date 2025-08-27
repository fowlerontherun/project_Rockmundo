# File: backend/routes/admin_job_routes.py
from fastapi import APIRouter, HTTPException, Request, Depends
from auth.dependencies import get_current_user_id, require_role
from utils.i18n import _
from services.admin_audit_service import audit_dependency

try:
    from jobs.world_pulse_jobs import run_daily_world_pulse, run_weekly_rollup
except Exception:
    run_daily_world_pulse = None
    run_weekly_rollup = None

try:
    from auth.dependencies import require_role
except Exception:
    def require_role(_roles):
        async def _ok():
            return True
        return _ok

router = APIRouter(
    prefix="/jobs", tags=["AdminJobs"], dependencies=[Depends(audit_dependency)]
)

@router.post("/world-pulse/daily")
async def trigger_world_pulse_daily(req: Request):
    if run_daily_world_pulse is None:
        raise HTTPException(status_code=501, detail=_("Daily job not available"))
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    await run_daily_world_pulse()
    return {"status": "ok", "job": "world_pulse_daily"}

@router.post("/world-pulse/weekly")
async def trigger_world_pulse_weekly(req: Request):
    if run_weekly_rollup is None:
        raise HTTPException(status_code=501, detail=_("Weekly job not available"))
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    await run_weekly_rollup()
    return {"status": "ok", "job": "world_pulse_weekly"}