"""API routes for World Pulse metrics.

These endpoints expose ranked lists of genres, trending movers and
sparkline series.  They are thin wrappers around
``WorldPulseService`` which handles all of the data gathering and
aggregation from the database.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

# The service lives under ``services`` when the package root is ``backend``.
try:  # pragma: no cover - import shim for tests vs runtime
    from services.jobs_world_pulse import WorldPulseService
    from services.world_pulse_service import get_current_season
except Exception:  # pragma: no cover
    from backend.services.jobs_world_pulse import WorldPulseService
    from backend.services.world_pulse_service import get_current_season


router = APIRouter(prefix="/world-pulse", tags=["World Pulse"])

# Instantiate the service once; it manages its own SQLite connections.
svc = WorldPulseService()


@router.get("/ranked")
def ranked_list(
    date: str = Query(..., description="YYYY-MM-DD of the snapshot"),
    region: str = Query("Global"),
    limit: int = Query(20, ge=1, le=100),
    period: str = Query("daily"),
    lookback: Optional[int] = Query(None, ge=1),
):
    """Return ranked list of genres for a given date/region."""
    try:
        return svc.ui_ranked_list(
            date=date,
            region=region,
            limit=limit,
            period=period,
            lookback=lookback,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/season")
def current_season() -> dict:
    """Expose the game's current season."""

    return {"season": get_current_season()}


@router.get("/trending")
def trending_genres(
    date: str = Query(..., description="YYYY-MM-DD of the snapshot"),
    region: str = Query("Global"),
    limit: int = Query(10, ge=1, le=100),
    period: str = Query("daily"),
    lookback: Optional[int] = Query(None, ge=1),
):
    """Return genres with biggest gains and losses."""
    try:
        return svc.ui_trending_movers(
            date=date,
            region=region,
            limit=limit,
            period=period,
            lookback=lookback,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sparkline")
def sparkline(
    date: str = Query(..., description="YYYY-MM-DD of the snapshot"),
    region: str = Query("Global"),
    period: str = Query("daily"),
    top_n: int = Query(5, ge=1, le=50),
    points: int = Query(14, ge=1, le=365),
):
    """Return sparkline time-series data for top genres."""
    try:
        return svc.sparkline_series(
            date=date,
            region=region,
            period=period,
            top_n=top_n,
            points=points,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


__all__ = ["router"]

