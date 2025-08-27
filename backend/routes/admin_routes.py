"""Aggregated admin router mounting all admin sub-routes."""

from fastapi import APIRouter

from .admin_analytics_routes import router as analytics_router
from .admin_business_routes import router as business_router
from .admin_economy_routes import router as economy_router
from .admin_job_routes import router as jobs_router
from .admin_media_moderation_routes import router as media_router
from .admin_npc_routes import router as npc_router
codex/expose-monitoring-metrics-in-backend
from .admin_monitoring_routes import router as monitoring_router



=======
from .admin_quest_routes import router as quest_router
codex/create-schema-and-preview-endpoints
from .admin_schema_routes import router as schema_router

codex/expose-monitoring-metrics-in-backend
router.include_router(monitoring_router)


