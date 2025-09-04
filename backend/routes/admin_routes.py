"""Aggregated admin router mounting all admin sub-routes."""

from fastapi import APIRouter, Depends, Request

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.admin_audit_service import audit_dependency
from backend.services.admin_analytics_service import fetch_shop_metrics

from .admin_analytics_routes import router as analytics_router
from .admin_apprenticeship_routes import router as apprenticeship_router
from .admin_audit_routes import router as audit_router
from .admin_book_routes import router as book_router
from .admin_business_routes import router as business_router
from .admin_course_routes import router as course_router
from .admin_city_shop_routes import router as city_shop_router
from .admin_player_shop_routes import router as player_shop_router
from .admin_loyalty_routes import router as loyalty_router
from .admin_workshop_routes import router as workshop_router
from .admin_economy_routes import router as economy_router
from .admin_item_routes import router as item_router
from .admin_job_routes import router as jobs_router
from .admin_media_moderation_routes import router as media_router
from .admin_modding_routes import router as modding_router
from .admin_monitoring_routes import router as monitoring_router
from .admin_music_routes import router as music_router
from .admin_name_routes import router as name_router
from .admin_npc_dialogue_routes import router as npc_dialogue_router
from .admin_npc_routes import router as npc_router
from .admin_online_tutorial_routes import router as online_tutorial_router
from .admin_quest_routes import router as quest_router
from .admin_schema_routes import router as schema_router
from .admin_song_popularity_routes import router as song_popularity_router
from .admin_tutor_routes import router as tutor_router
from .admin_venue_routes import router as venue_router
from .admin_xp_event_routes import router as xp_event_router
from .admin_xp_routes import router as xp_router

router = APIRouter()


@router.get("/economy/analytics", dependencies=[Depends(audit_dependency)])
async def economy_analytics(
    req: Request,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int = 5,
):
    """Summary of shop sales and top items."""

    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return fetch_shop_metrics(period_start, period_end, limit)


router.include_router(analytics_router)
router.include_router(audit_router)
router.include_router(business_router)
router.include_router(city_shop_router)
router.include_router(player_shop_router)
router.include_router(loyalty_router)
router.include_router(economy_router)
router.include_router(xp_router)
router.include_router(xp_event_router)
router.include_router(jobs_router)
router.include_router(media_router)
router.include_router(monitoring_router)
router.include_router(modding_router)
router.include_router(npc_router)
router.include_router(npc_dialogue_router)
router.include_router(quest_router)
router.include_router(schema_router)
router.include_router(song_popularity_router)
router.include_router(item_router)

router.include_router(course_router)
router.include_router(book_router)
router.include_router(workshop_router)
router.include_router(online_tutorial_router)
router.include_router(tutor_router)
router.include_router(apprenticeship_router)

router.include_router(venue_router)
router.include_router(music_router)
router.include_router(name_router)

