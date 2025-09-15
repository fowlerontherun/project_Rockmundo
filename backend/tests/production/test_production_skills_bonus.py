from backend.services.music_production_service import MusicProductionService
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID


class DummyAvatar:
    def __init__(self, tech_savvy: int = 0):
        self.tech_savvy = tech_savvy


class DummyAvatarService:
    def __init__(self, tech_savvy: int = 0):
        self.avatar = DummyAvatar(tech_savvy)

    def get_avatar(self, _band_id):
        return self.avatar


def _set_skills(band_id: int, level: int) -> None:
    for name in ["music_production", "mixing", "mastering"]:
        sid = SKILL_NAME_TO_ID[name]
        skill_service._skills[(band_id, sid)] = Skill(
            id=sid,
            name=name,
            category="creative",
            xp=(level - 1) * 100,
            level=level,
        )


def test_production_skills_reduce_time_and_boost_xp():
    svc = MusicProductionService(avatar_service=DummyAvatarService(0))
    skill_service._skills.clear()
    _set_skills(1, 1)
    low = svc.produce_track(1, base_minutes=120, base_xp=20)
    _set_skills(2, 80)
    high = svc.produce_track(2, base_minutes=120, base_xp=20)
    assert high["time_minutes"] < low["time_minutes"]
    assert high["xp_gain"] > low["xp_gain"]
