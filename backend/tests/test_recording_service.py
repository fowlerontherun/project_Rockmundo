import pytest

from backend.services.recording_service import RecordingService


class DummyEconomy:
    def ensure_schema(self) -> None:
        pass

    def withdraw(self, *args, **kwargs) -> None:
        pass


class StubChem:
    def __init__(self, score):
        self.score = score

    def initialize_pair(self, a, b):
        return type("P", (), {"score": self.score})()

    def adjust_pair(self, a, b, d):
        return self.initialize_pair(a, b)


def _run_session(score):
    svc = RecordingService(economy=DummyEconomy(), chemistry_service=StubChem(score))
    session = svc.schedule_session(1, "Studio", "2024-01-01", "2024-01-02", [1], 0)
    svc.assign_personnel(session.id, 1)
    svc.assign_personnel(session.id, 2)
    svc.update_track_status(session.id, 1, "recorded")
    return session


def test_environment_quality_scales_with_chemistry():
    high = _run_session(90)
    low = _run_session(10)
    assert high.environment_quality == pytest.approx(1.4)
    assert low.environment_quality == pytest.approx(0.6)
