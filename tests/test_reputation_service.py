import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

import pytest

from backend.services.reputation_service import ReputationService
from backend.services import event_service


def test_reputation_accumulation_and_elite_unlock(tmp_path):
    db = tmp_path / "rep.sqlite"
    svc = ReputationService(db_path=db)
    # Make event_service use this test instance
    event_service.reputation_service = svc

    user_id = 1

    # Initially not enough reputation
    with pytest.raises(PermissionError):
        event_service.schedule_elite_event(user_id, {"name": "vip gig"})

    # Award reputation via different activities
    svc.record_gig(user_id)
    svc.record_release(user_id)
    svc.record_achievement(user_id)

    assert svc.get_reputation(user_id) == 60
    assert len(svc.get_history(user_id)) == 3

    # Accumulate additional gigs until threshold met
    while svc.get_reputation(user_id) < event_service.ELITE_REPUTATION_THRESHOLD:
        svc.record_gig(user_id)

    evt = event_service.schedule_elite_event(user_id, {"name": "vip gig"})
    assert evt["name"] == "vip gig"
