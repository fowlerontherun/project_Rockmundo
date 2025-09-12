from fastapi import APIRouter

from services.achievement_service import AchievementService

router = APIRouter(prefix="/achievements", tags=["Achievements"])
svc = AchievementService()


@router.get("/")
def list_achievements():
    """Return all available achievements."""
    return svc.list_achievements()


@router.get("/user/{user_id}")
def user_achievements(user_id: int):
    """Return achievement progress for a specific user."""
    return svc.get_user_achievements(user_id)
