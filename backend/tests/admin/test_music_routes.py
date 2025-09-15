import asyncio
import importlib
import sys
import types

from fastapi import Request

import seeds.skill_seed as skill_seed


def test_add_and_delete_skill(monkeypatch):
    dummy_genre_seed = types.SimpleNamespace(SEED_GENRES=[], GENRE_NAME_TO_ID={})
    dummy_equipment_seed = types.SimpleNamespace(
        SEED_STAGE_EQUIPMENT=[], STAGE_EQUIPMENT_NAME_TO_ID={}
    )
    monkeypatch.setitem(sys.modules, "seeds.genre_seed", dummy_genre_seed)
    monkeypatch.setitem(
        sys.modules, "seeds.stage_equipment_seed", dummy_equipment_seed
    )

    admin_music_routes = importlib.import_module("routes.admin_music_routes")

    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(admin_music_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(admin_music_routes, "require_permission", fake_require_permission)

    req = Request({"type": "http"})

    original_skills = list(skill_seed.SEED_SKILLS)
    try:
        start_len = len(skill_seed.SEED_SKILLS)
        start_max = max(s.id for s in skill_seed.SEED_SKILLS)

        prereq_id = skill_seed.SEED_SKILLS[0].id
        new_schema = admin_music_routes.SkillSchema(
            name="test_skill",
            category="instrument",
            prerequisites={prereq_id: 100},
        )
        asyncio.run(admin_music_routes.add_skill(new_schema, req))
        assert len(skill_seed.SEED_SKILLS) == start_len + 1
        added = skill_seed.SEED_SKILLS[-1]
        assert added.name == "test_skill"
        assert added.id == start_max + 1
        assert added.prerequisites == {prereq_id: 100}
        assert skill_seed.SKILL_NAME_TO_ID["test_skill"] == added.id

        other_schema = admin_music_routes.SkillSchema(name="other_skill", category="instrument")
        asyncio.run(admin_music_routes.add_skill(other_schema, req))
        ids = [s.id for s in skill_seed.SEED_SKILLS]
        assert len(ids) == len(set(ids))

        asyncio.run(admin_music_routes.delete_skill(added.id, req))
        assert all(s.id != added.id for s in skill_seed.SEED_SKILLS)
        assert "test_skill" not in skill_seed.SKILL_NAME_TO_ID
    finally:
        skill_seed.SEED_SKILLS = original_skills
        skill_seed.SKILL_NAME_TO_ID = {s.name: s.id for s in skill_seed.SEED_SKILLS}

