# File: backend/routes/admin_job_routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from utils.i18n import _

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

router = APIRouter(prefix="/admin/jobs", tags=["AdminJobs"])

@router.post("/world-pulse/daily", dependencies=[Depends(require_role(["admin"]))])
async def trigger_world_pulse_daily():
    if run_daily_world_pulse is None:
        raise HTTPException(status_code=501, detail=_("Daily job not available"))
    await run_daily_world_pulse()
    return {"status": "ok", "job": "world_pulse_daily"}

@router.post("/world-pulse/weekly", dependencies=[Depends(require_role(["admin"]))])
async def trigger_world_pulse_weekly():
    if run_weekly_rollup is None:
        raise HTTPException(status_code=501, detail=_("Weekly job not available"))
    await run_weekly_rollup()
    return {"status": "ok", "job": "world_pulse_weekly"}