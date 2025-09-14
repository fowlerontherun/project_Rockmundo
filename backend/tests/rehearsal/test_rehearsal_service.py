import sqlite3
from services.rehearsal_service import RehearsalService
from services import event_service


def _setup(tmp_path):
    db = tmp_path / "test.db"
    svc = RehearsalService(db)
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO bands (id, name) VALUES (1, 'Test')")
    return svc, db


def test_booking_collision(tmp_path):
    svc, _ = _setup(tmp_path)
    svc.book_session(1, "2024-01-01T10:00:00", "2024-01-01T12:00:00", [])
    try:
        svc.book_session(1, "2024-01-01T11:00:00", "2024-01-01T13:00:00", [])
    except ValueError:
        collision = True
    else:
        collision = False
    assert collision, "expected booking conflict"


def test_practice_bonus(tmp_path):
    svc, db = _setup(tmp_path)
    result = svc.book_session(
        1, "2024-01-02T10:00:00", "2024-01-02T11:00:00", [1, 2, 3]
    )
    assert result["bonus"] == 1.5
    with sqlite3.connect(db) as conn:
        skill, quality = conn.execute(
            "SELECT skill, performance_quality FROM bands WHERE id=1"
        ).fetchone()
    assert skill == 1.5
    assert quality == 0.75


def test_blocked_skill(tmp_path, monkeypatch):
    svc, db = _setup(tmp_path)
    monkeypatch.setattr(
        "backend.services.rehearsal_service.is_skill_blocked", lambda *_: True
    )
    svc.book_session(1, "2024-01-03T10:00:00", "2024-01-03T11:00:00", [1, 2])
    with sqlite3.connect(db) as conn:
        skill, quality = conn.execute(
            "SELECT skill, performance_quality FROM bands WHERE id=1"
        ).fetchone()
    assert skill == 0
    assert quality == 0.5

