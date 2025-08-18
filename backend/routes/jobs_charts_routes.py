# File: backend/routes/jobs_charts_routes.py
from fastapi import APIRouter, HTTPException, Depends
from services.jobs_charts import ChartsJobsService

# Auth dep
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/admin/jobs", tags=["Admin Jobs"])
svc = ChartsJobsService()

@router.post("/charts/daily", dependencies=[Depends(require_role(["admin","moderator"]))])
def charts_daily(date: str):
    """
    Compute charts for a single day. date: 'YYYY-MM-DD'
    """
    try:
        return svc.run_daily(date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/charts/weekly", dependencies=[Depends(require_role(["admin","moderator"]))])
def charts_weekly(week_end_date: str):
    """
    Compute charts for the week ending on the given date (expected Sunday), format 'YYYY-MM-DD'.
    """
    try:
        return svc.run_weekly(week_end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
