"""Admin endpoints for managing seasonal score multipliers."""

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import require_permission
from backend.database import get_conn
from backend.services.season_service import activate_season, deactivate_season

router = APIRouter(
    prefix="/season",
    tags=["AdminSeason"],
    dependencies=[Depends(require_permission(["admin"]))],
)


def _conn():
    return get_conn()


@router.post("/{season}/activate")
def activate(season: str, conn=Depends(_conn)) -> dict:
    if not activate_season(conn, season):
        raise HTTPException(status_code=404, detail="season not found")
    return {"status": "activated", "season": season}


@router.post("/{season}/deactivate")
def deactivate(season: str, conn=Depends(_conn)) -> dict:
    if not deactivate_season(conn, season):
        raise HTTPException(status_code=404, detail="season not found")
    return {"status": "deactivated", "season": season}


__all__ = ["router", "activate", "deactivate"]
