from backend.services.music_production_service import MusicProductionService
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID


class DummyAvatar:
    def __init__(self, tech_savvy: int):
        self.tech_savvy = tech_savvy


class DummyAvatarService:
    def __init__(self, tech_savvy: int):
        self.avatar = DummyAvatar(tech_savvy)

    def get_avatar(self, _band_id):
        return self.avatar


def test_sound_design_reduces_time_and_boosts_quality():
    svc = MusicProductionService(avatar_service=DummyAvatarService(0))
    user_id = 1
    skill_service._skills.clear()

    base = svc.produce_track(1, base_minutes=120, user_id=user_id)
    skill_service.train(
        user_id,
        Skill(id=SKILL_NAME_TO_ID["sound_design"], name="sound_design", category="creative"),
        500,
    )
    advanced = svc.produce_track(1, base_minutes=120, user_id=user_id)

    assert advanced["time_minutes"] < base["time_minutes"]
    assert advanced["quality"] > base["quality"]
