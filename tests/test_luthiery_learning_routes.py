import pytest
from fastapi import HTTPException

import routes.learning_routes as routes
from seeds.skill_seed import SKILL_NAME_TO_ID


def test_luthiery_tree_contains_every_skill(monkeypatch):
    monkeypatch.setattr(routes.svc, "get_skill_level", lambda _character, _skill: 1)
    result = routes.luthiery_tree(character_id=101)
    keys = {row["key"] for row in result["skills"]}
    assert keys == set(routes.SKILL_DESCRIPTIONS)
    assert set(result["rewards"]) == {"materials", "shapes", "finishes", "components"}


def test_learning_rejects_forged_skill_metadata():
    payload = routes.SessionRequest(
        user_id=101,
        skill_id=SKILL_NAME_TO_ID["advanced_luthiery"],
        skill_name="luthiery",
        skill_category="craftsmanship",
        method="book",
        duration=1,
    )
    with pytest.raises(HTTPException) as exc:
        routes.enqueue_session(payload, character_id=101)
    assert exc.value.status_code == 400


def test_learning_rejects_other_selected_character():
    payload = routes.SessionRequest(
        user_id=202,
        skill_id=SKILL_NAME_TO_ID["luthiery"],
        skill_name="luthiery",
        skill_category="craftsmanship",
        method="book",
        duration=1,
    )
    with pytest.raises(HTTPException) as exc:
        routes.enqueue_session(payload, character_id=101)
    assert exc.value.status_code == 403
