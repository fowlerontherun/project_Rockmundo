from services.music_production_service import MusicProductionService


class DummyAvatar:
    def __init__(self, tech_savvy: int):
        self.tech_savvy = tech_savvy


class DummyAvatarService:
    def __init__(self, tech_savvy: int):
        self.avatar = DummyAvatar(tech_savvy)

    def get_avatar(self, _band_id):
        return self.avatar


def test_tech_savvy_reduces_production_time_and_stamina():
    svc_low = MusicProductionService(avatar_service=DummyAvatarService(0))
    svc_high = MusicProductionService(avatar_service=DummyAvatarService(80))
    result_low = svc_low.produce_track(1, base_minutes=120, base_stamina_cost=20)
    result_high = svc_high.produce_track(1, base_minutes=120, base_stamina_cost=20)
    assert result_high["time_minutes"] < result_low["time_minutes"]
    assert result_high["stamina_cost"] < result_low["stamina_cost"]
    assert result_high["xp_gain"] > result_low["xp_gain"]
