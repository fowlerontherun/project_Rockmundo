from services import event_service

def test_roll_for_daily_event_trigger(monkeypatch):
    monkeypatch.setattr(event_service.random, "random", lambda: 0.0)
    event = event_service.roll_for_daily_event(1, {"drinking": "high"}, ["vocals"])
    assert event is not None
    assert event["event"] == "vocal fatigue"


def test_roll_for_daily_event_none(monkeypatch):
    monkeypatch.setattr(event_service.random, "random", lambda: 1.0)
    event = event_service.roll_for_daily_event(1, {"drinking": "low"}, [])
    assert event is None
