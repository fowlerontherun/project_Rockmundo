# File: backend/routes/jobs_routes.py
from fastapi import APIRouter, HTTPException, Depends
from services.jobs_royalties import RoyaltyJobsService, RoyaltyJobError

# Auth dep
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/admin/jobs", tags=["Admin Jobs"])
svc = RoyaltyJobsService()

@router.post("/royalties/run", dependencies=[Depends(require_role(["admin","moderator"]))])
def run_royalties(period_start: str, period_end: str):
    """
    Trigger a royalty run for [period_start, period_end] (YYYY-MM-DD).
    """
    try:
        res = svc.run_royalties(period_start, period_end)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
