import types

from backend.services.random_event_service import RandomEventService


class DummyDB:
    def __init__(self):
        self.inserted = []
        self.fame = {}
        self.funds = {}
        self.band_ids = [1, 2]

    def insert_random_event(self, event):
        self.inserted.append(event)

    def increase_band_fame(self, band_id, amount):
        self.fame[band_id] = self.fame.get(band_id, 0) + amount

    def increase_band_funds(self, band_id, amount):
        self.funds[band_id] = self.funds.get(band_id, 0) + amount

    def list_band_ids(self):
        return self.band_ids


class DummyNotifier:
    def __init__(self):
        self.created = []

    def create(self, user_id, title, body):
        self.created.append((user_id, title, body))
        return 1


def test_run_scheduled_events_frequency(monkeypatch):
    db = DummyDB()
    notifier = DummyNotifier()
    service = RandomEventService(db, notifier)
    monkeypatch.setattr("backend.services.random_event_service.random.random", lambda: 0.0)
    count = service.run_scheduled_events()
    assert count == len(db.band_ids)
    assert len(db.inserted) == len(db.band_ids)


def test_trigger_event_applies_outcome(monkeypatch):
    db = DummyDB()
    notifier = DummyNotifier()
    service = RandomEventService(db, notifier)
    options = [("press", "press", {"fame": 5})]
    monkeypatch.setattr("backend.services.random_event_service.random.choice", lambda _: options[0])
    event = service.trigger_event_for_band(1, user_id=42)
    assert db.fame[1] == 5
    assert notifier.created[0][0] == 42
    assert event["fame"] == 5
