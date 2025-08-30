import sqlite3

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


def test_apply_and_block(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(event_service, "DB_PATH", db)
    event_service.apply_event_effect(
        1, {"effect": "block_skill", "skill": "guitar", "duration": 1}
    )
    assert event_service.is_skill_blocked(1, "guitar")


def test_clear_expired(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(event_service, "DB_PATH", db)
    event_service.apply_event_effect(
        1, {"effect": "block_skill", "skill": "guitar", "duration": 1}
    )
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE event_effects SET start_date = datetime('now', '-10 days')"
        )
    deleted = event_service.clear_expired_events()
    assert deleted == 1
    assert not event_service.is_skill_blocked(1, "guitar")
