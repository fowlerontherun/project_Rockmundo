import sys
import types

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

# Stub all sub-route modules imported by admin_routes to avoid heavy dependencies
SUB_MODULES = [
    "backend.routes.admin_analytics_routes",
    "backend.routes.admin_apprenticeship_routes",
    "backend.routes.admin_audit_routes",
    "backend.routes.admin_book_routes",
    "backend.routes.admin_business_routes",
    "backend.routes.admin_city_shop_routes",
    "backend.routes.admin_course_routes",
    "backend.routes.admin_economy_routes",
    "backend.routes.admin_item_routes",
    "backend.routes.admin_drug_routes",
    "backend.routes.admin_job_routes",
    "backend.routes.admin_loyalty_routes",
    "backend.routes.admin_media_moderation_routes",
    "backend.routes.admin_modding_routes",
    "backend.routes.admin_monitoring_routes",
    "backend.routes.admin_music_routes",
    "backend.routes.admin_name_routes",
    "backend.routes.admin_npc_dialogue_routes",
    "backend.routes.admin_npc_routes",
    "backend.routes.admin_online_tutorial_routes",
    "backend.routes.admin_player_shop_routes",
    "backend.routes.admin_quest_routes",
    "backend.routes.admin_schema_routes",
    "backend.routes.admin_shop_event_routes",
    "backend.routes.admin_song_popularity_routes",
    "backend.routes.admin_tutor_routes",
    "backend.routes.admin_venue_routes",
    "backend.routes.admin_workshop_routes",
    "backend.routes.admin_xp_event_routes",
    "backend.routes.admin_xp_routes",
]

for name in SUB_MODULES:
    mod = types.ModuleType(name)
    mod.router = APIRouter()
    sys.modules[name] = mod

from backend.routes import admin_routes


def test_admin_router_requires_admin(monkeypatch):
    app = FastAPI()
    app.include_router(admin_routes.router)

    async def fake_current_user(_req):
        return 1

    async def fail_permission(perms, user_id):
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    async def noop_audit_dependency():
        return None

    # Patch functions called inside the route
    monkeypatch.setattr(admin_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(admin_routes, "require_permission", fail_permission)
    app.dependency_overrides[admin_routes.audit_dependency] = noop_audit_dependency

    client = TestClient(app)
    resp = client.get("/admin/economy/analytics")
    assert resp.status_code == 403
