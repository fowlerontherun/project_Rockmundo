"""Aggregated admin router mounting all admin sub-routes."""

from fastapi import APIRouter

from .admin_analytics_routes import router as analytics_router
from .admin_audit_routes import router as audit_router
from .admin_business_routes import router as business_router
from .admin_economy_routes import router as economy_router
from .admin_job_routes import router as jobs_router
from .admin_media_moderation_routes import router as media_router
from .admin_monitoring_routes import router as monitoring_router
from .admin_music_routes import router as music_router
from .admin_npc_routes import router as npc_router
from .admin_quest_routes import router as quest_router
from .admin_schema_routes import router as schema_router
from .admin_venue_routes import router as venue_router
from .admin_xp_event_routes import router as xp_event_router
from .admin_xp_routes import router as xp_router

router = APIRouter()

router.include_router(analytics_router)
router.include_router(audit_router)
router.include_router(business_router)
router.include_router(economy_router)
router.include_router(xp_router)
router.include_router(xp_event_router)
router.include_router(jobs_router)
router.include_router(media_router)
router.include_router(monitoring_router)
router.include_router(npc_router)
router.include_router(quest_router)
router.include_router(schema_router)
router.include_router(venue_router)
router.include_router(music_router)

