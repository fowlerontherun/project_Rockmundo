# File: backend/routes/world_pulse_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from services.jobs_world_pulse import WorldPulseService

# Auth dependency (replace with real one in your app)
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/pulse", tags=["World Pulse"])
svc = WorldPulseService()
svc.ensure_schema()

# Admin
@router.post("/admin/run-daily", dependencies=[Depends(require_role(["admin","moderator"]))])
def run_daily(date: str):
    try:
        return svc.run_daily(date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/run-weekly", dependencies=[Depends(require_role(["admin","moderator"]))])
def run_weekly(week_end_date: str):
    try:
        return svc.run_weekly(week_end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/run-all", dependencies=[Depends(require_role(["admin","moderator"]))])
def run_all(date: str):
    try:
        return svc.run_all(date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Read
@router.get("/genres/top")
def top_genres(date: str, region: str = "Global", limit: int = 20, period: str = "daily"):
    try:
        return svc.top_genres(date=date, region=region, limit=limit, period=period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/genres/trending")
def trending(date: str, region: str = "Global", limit: int = 20, lookback: int = 7, period: str = "daily"):
    try:
        return svc.trending(date=date, region=region, limit=limit, lookback=lookback, period=period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# UI helpers
@router.get("/ui/top")
def ui_top(date: str, region: str = "Global", limit: int = 20, period: str = "daily", lookback: Optional[int] = None):
    try:
        return svc.ui_ranked_list(date=date, region=region, limit=limit, period=period, lookback=lookback)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ui/trending")
def ui_trending(date: str, region: str = "Global", limit: int = 10, period: str = "daily", lookback: Optional[int] = None):
    try:
        return svc.ui_trending_movers(date=date, region=region, limit=limit, period=period, lookback=lookback)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ui/sparkline")
def ui_sparkline(date: str, region: str = "Global", period: str = "daily", top_n: int = 5, points: int = 14):
    """
    Returns sparkline-ready time-series for the top N genres on 'date':
    {"period":"daily","region":"Global","dates":[...],"series":[{"genre":"Rock","values":[...]}, ...]}
    """
    try:
        return svc.sparkline_series(date=date, region=region, period=period, top_n=top_n, points=points)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
