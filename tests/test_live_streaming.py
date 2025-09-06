from backend.services import streaming_service as ss
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID


def test_live_stream_skill_improves_quality():
    skill_service._skills.clear()
    skill_service._xp_today.clear()

    base = ss.perform_live_stream(user_id=1, duration_minutes=10, base_viewers=100)
    base_retained = base["retained_viewers"]
    base_tips = base["tips"]

    skill = Skill(
        id=SKILL_NAME_TO_ID["live_streaming"],
        name="live_streaming",
        category="performance",
    )
    skill_service.train(1, skill, 500)

    boosted = ss.perform_live_stream(user_id=1, duration_minutes=10, base_viewers=100)
    assert boosted["retained_viewers"] > base_retained
    assert boosted["tips"] > base_tips

