"""Aggregated admin router mounting all admin sub-routes."""

from fastapi import APIRouter

from .admin_analytics_routes import router as analytics_router
from .admin_job_routes import router as jobs_router
from .admin_media_moderation_routes import router as media_router
from .admin_npc_routes import router as npc_router


router = APIRouter()

# Mount individual admin feature routers
router.include_router(analytics_router)
router.include_router(jobs_router)
router.include_router(media_router)
router.include_router(npc_router)

