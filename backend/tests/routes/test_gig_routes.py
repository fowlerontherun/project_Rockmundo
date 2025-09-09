from datetime import date, time
import types
import sys

import pytest


def load_gig_module(monkeypatch):
    """Import the gig routes module with minimal dependencies."""

    # Dummy router to avoid FastAPI side effects during import
    class DummyRouter:
        def __init__(self, *args, **kwargs):
            pass
        def post(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

        def get(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

        def websocket(self, *args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

    monkeypatch.setattr("fastapi.APIRouter", DummyRouter)

    # Stub auth dependencies to avoid auth logic during import
    from auth import dependencies as deps

    def fake_require_permission(_roles):
        def _dep():
            return True

        return _dep

    deps.require_permission = fake_require_permission
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

    # Provide a simple Venue model for capacity lookups
    venue_module = types.ModuleType("models.venues")

    class Venue:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", 0)
            self.capacity = kwargs.get("capacity", 100)

    venue_module.Venue = Venue
    sys.modules["models.venues"] = venue_module

    # Minimal i18n utility
    i18n_module = types.ModuleType("utils.i18n")
    i18n_module._ = lambda s: s
    sys.modules["utils.i18n"] = i18n_module

    # Stub band, fame, notifications and skill services to avoid heavy imports
    band_service_module = types.ModuleType("services.band_service")

    class BandService:
        def get_band_info(self, band_id):
            return {"id": band_id, "fame": 0, "members": []}

    band_service_module.BandService = BandService
    sys.modules["services.band_service"] = band_service_module

    fame_service_module = types.ModuleType("services.fame_service")

    class FameService:
        def __init__(self, db):
            self.db = db

        def get_total_fame(self, band_id):
            return 0

    fame_service_module.FameService = FameService
    sys.modules["services.fame_service"] = fame_service_module

    skill_service_module = types.ModuleType("services.skill_service")

    class _SkillResult:
        def __init__(self, lvl=0):
            self.level = lvl

    class SkillService:
        def train(self, uid, skill, xp):
            return _SkillResult(0)

        def get_skill_level(self, uid, skill):
            return 0

    skill_service_module.skill_service = SkillService()
    sys.modules["services.skill_service"] = skill_service_module

    notif_module = types.ModuleType("services.notifications_service")

    class NotificationsService:
        def create(self, *args, **kwargs):
            pass

    notif_module.NotificationsService = NotificationsService
    sys.modules["services.notifications_service"] = notif_module

    # Minimal database module with get_db placeholder
    db_module = types.ModuleType("database")

    def _dummy_get_db():
        raise RuntimeError("get_db should be overridden in tests")

    db_module.get_db = _dummy_get_db
    sys.modules["database"] = db_module

    # Remove cached module if reloading
    sys.modules.pop("routes.gig", None)
    import routes.gig as gig_routes

    # Default patches to bypass DB logic in tests
    gig_routes.get_venue_capacity = lambda venue_id, db: 100
    gig_routes.band_has_conflict = lambda *a, **k: False
    gig_routes.venue_has_conflict = lambda *a, **k: False

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
        defaults = {
            "start_time": time(20, 0),
            "end_time": time(22, 0),
            "guarantee": 0.0,
            "ticket_split": 0.0,
            "expected_audience": 0,
        }
        defaults.update(kwargs)
        self.__dict__.update(defaults)

    def dict(self):
        return self.__dict__


def test_book_acoustic_gig_solo_band(monkeypatch):
    gig_routes = load_gig_module(monkeypatch)
    db = DummySession()

    # Solo band with sufficient skill should pass
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id: True)
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id: 80
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
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id: False)
    monkeypatch.setattr(
        gig_routes.fame_service, "get_total_fame", lambda band_id: 200
    )
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id: 80
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


def test_book_acoustic_gig_solo_band_insufficient(monkeypatch):
    gig_routes = load_gig_module(monkeypatch)
    db = DummySession()

    # Solo band with low skill should raise HTTPException
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id: True)
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id: 60
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


def test_book_acoustic_gig_non_solo_sufficient(monkeypatch):
    gig_routes = load_gig_module(monkeypatch)
    db = DummySession()

    # Non-solo band with sufficient fame and skill should pass
    monkeypatch.setattr(gig_routes, "is_band_solo", lambda band_id: False)
    monkeypatch.setattr(
        gig_routes.fame_service, "get_total_fame", lambda band_id: 400
    )
    monkeypatch.setattr(
        gig_routes, "get_band_acoustic_skill_score", lambda band_id: 75
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

