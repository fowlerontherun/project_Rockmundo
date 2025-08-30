from fastapi import APIRouter

from services.legacy_service import LegacyService

router = APIRouter(prefix="/legacy", tags=["Legacy"])
service = LegacyService()
service.ensure_schema()


@router.get("/{band_id}")
def get_band_legacy(band_id: int):
    """Return legacy milestones and total score for a band."""
    return {
        "band_id": band_id,
        "score": service.compute_score(band_id),
        "milestones": service.get_history(band_id),
    }


@router.get("/leaderboard")
def get_leaderboard(limit: int = 10):
    """Hall-of-fame style leaderboard."""
    return service.get_leaderboard(limit)
