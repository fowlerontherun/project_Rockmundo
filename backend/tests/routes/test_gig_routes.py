from datetime import date
import types
import sys

import pytest


def load_gig_module(monkeypatch):
    """Import the gig routes module with minimal dependencies."""

    # Dummy router to avoid FastAPI side effects during import
    class DummyRouter:
        def post(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

        def get(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

    monkeypatch.setattr("fastapi.APIRouter", DummyRouter)

    # Stub auth dependencies to avoid auth logic during import
    from auth import dependencies as deps

    def fake_require_role(_roles):
        def _dep():
            return True

        return _dep

    deps.require_role = fake_require_role
    deps.get_current_user_id = lambda: 1

    # Provide a simple Gig model to bypass SQLAlchemy
    gig_module = types.ModuleType("models.gig")

    class Gig:
        def __init__(self, **kwargs):
            # Defaults expected by GigOut
            self.id = 0
            self.audience_size = 0
            self.total_earned = 0.0
            self.review = None
            for k, v in kwargs.items():
                setattr(self, k, v)

    gig_module.Gig = Gig
    sys.modules["models.gig"] = gig_module

    # Minimal database module with get_db placeholder
    db_module = types.ModuleType("database")

    def _dummy_get_db():
        raise RuntimeError("get_db should be overridden in tests")

    db_module.get_db = _dummy_get_db
    sys.modules["database"] = db_module

    # Remove cached module if reloading
    sys.modules.pop("routes.gig", None)
    import routes.gig as gig_routes

    return gig_routes


class DummySession:
    def add(self, obj):
        self.obj = obj

    def commit(self):
        pass

    def refresh(self, obj):
        obj.id = 1


class DummyGigCreate:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dict(self):
        return self.__dict__


def test_book_acoustic_gig_solo_band(monkeypatch):
    gig_routes = load_gig_module(monkeypatch)
    db = DummySession()

    # Solo band with sufficient skill should pass
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id, db: True)
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id, db: 80
    )

    gig = DummyGigCreate(
        band_id=1,
        venue_id=2,
        date=date(2024, 1, 1),
        ticket_price=10.0,
        acoustic=True,
    )

    result = gig_routes.book_gig(gig, db, user_id=1)
    assert result.acoustic is True


def test_book_acoustic_gig_non_solo_insufficient(monkeypatch):
    gig_routes = load_gig_module(monkeypatch)
    db = DummySession()

    # Non-solo band with low fame should raise HTTPException
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id, db: False)
    monkeypatch.setattr(gig_routes, "get_band_fame", lambda band_id, db: 200)
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id, db: 80
    )

    gig = DummyGigCreate(
        band_id=1,
        venue_id=2,
        date=date(2024, 1, 1),
        ticket_price=10.0,
        acoustic=True,
    )

    with pytest.raises(Exception) as exc:
        gig_routes.book_gig(gig, db, user_id=1)

    assert getattr(exc.value, "status_code", None) == 403

