from datetime import datetime, timedelta

import pytest

from backend.models.xp_event import XPEvent
from backend.services.xp_event_service import XPEventService


def test_additive_stacking(tmp_path):
    svc = XPEventService(path=tmp_path / "xp_events.json")
    now = datetime.utcnow()
    svc.create_event(
        XPEvent(
            id=None,
            name="double",
            start_time=now,
            end_time=now + timedelta(hours=1),
            multiplier=2.0,
        )
    )
    svc.create_event(
        XPEvent(
            id=None,
            name="triple",
            start_time=now,
            end_time=now + timedelta(hours=1),
            multiplier=3.0,
        )
    )

    assert svc.get_active_multiplier() == pytest.approx(4.0)
