import asyncio
import importlib
import sys
import types

from fastapi import Request

import backend.seeds.skill_seed as skill_seed
from backend.models import skill_seed_store


def test_skills_persist_across_restarts(tmp_path, monkeypatch):
    # Use temporary path for the seed store
    monkeypatch.setattr(
        skill_seed_store,
        "SKILL_SEED_PATH",
        tmp_path / "skill_seed.json",
        raising=False,
    )

    # Dummy modules for unrelated seeds
    dummy_genre_seed = types.SimpleNamespace(SEED_GENRES=[], GENRE_NAME_TO_ID={})
    dummy_equipment_seed = types.SimpleNamespace(
        SEED_STAGE_EQUIPMENT=[], STAGE_EQUIPMENT_NAME_TO_ID={}
    )
    monkeypatch.setitem(sys.modules, "backend.seeds.genre_seed", dummy_genre_seed)
    monkeypatch.setitem(
        sys.modules, "backend.seeds.stage_equipment_seed", dummy_equipment_seed
    )

    admin_music_routes = importlib.import_module("backend.routes.admin_music_routes")

    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(admin_music_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(admin_music_routes, "require_permission", fake_require_permission)

    req = Request({"type": "http"})

    new_schema = admin_music_routes.SkillSchema(
        name="persisted_skill", category="instrument"
    )
    asyncio.run(admin_music_routes.add_skill(new_schema, req))

    assert skill_seed_store.SKILL_SEED_PATH.exists()

    # Simulate restart by reloading modules
    importlib.reload(skill_seed)
    del sys.modules["backend.routes.admin_music_routes"]
    admin_music_routes = importlib.import_module("backend.routes.admin_music_routes")

    assert any(s.name == "persisted_skill" for s in skill_seed.SEED_SKILLS)

    # Cleanup
    importlib.reload(skill_seed)
