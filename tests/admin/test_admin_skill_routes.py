import asyncio
import importlib
import sys
import types
from pathlib import Path

from fastapi import Request

BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

import backend.seeds.skill_seed as skill_seed
from backend.models import skill_seed_store


def test_prerequisites_persist_across_restarts(tmp_path, monkeypatch):
    # Use temporary file for skill persistence
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

    skill_id = skill_seed.SEED_SKILLS[0].id
    update = admin_music_routes.SkillPrerequisitesSchema(prerequisites={2: 3})
    asyncio.run(admin_music_routes.update_skill_prerequisites(skill_id, update, req))

    assert skill_seed_store.SKILL_SEED_PATH.exists()
    assert any(s.prerequisites.get(2) == 3 for s in skill_seed.SEED_SKILLS)

    # Simulate restart
    importlib.reload(skill_seed)
    del sys.modules["backend.routes.admin_music_routes"]
    admin_music_routes = importlib.import_module("backend.routes.admin_music_routes")

    reloaded_skill = next(s for s in skill_seed.SEED_SKILLS if s.id == skill_id)
    assert reloaded_skill.prerequisites.get(2) == 3

    # Cleanup
    importlib.reload(skill_seed)
