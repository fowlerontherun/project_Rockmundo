from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.recording_service import RecordingService
from backend.services.skill_service import skill_service


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


def test_recording_skill_influences_cost_quality():
    svc = RecordingService()
    skill_service._skills.clear()
    # Ensure both bands have funds
    svc.economy.deposit(1, 10_000)
    svc.economy.deposit(2, 10_000)
    _set_skills(1, 80)
    _set_skills(2, 1)
    high = svc.schedule_session(1, "A", "s", "e", [1], cost_cents=1000)
    low = svc.schedule_session(2, "A", "s", "e", [1], cost_cents=1000)
    assert high.environment_quality > low.environment_quality
    assert high.cost_cents < low.cost_cents
    # Update tracks through mixing and mastering
    svc.update_track_status(high.id, 1, "mixed")
    svc.update_track_status(low.id, 1, "mixed")
    svc.update_track_status(high.id, 1, "mastered")
    svc.update_track_status(low.id, 1, "mastered")
    assert high.track_quality[1] > low.track_quality[1]
