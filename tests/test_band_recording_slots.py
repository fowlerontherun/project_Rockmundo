import pathlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ensure backend package importable
root_path = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(root_path))

# Stub auth dependency modules expected by band routes
import types

auth_mod = types.ModuleType("auth")
deps_mod = types.ModuleType("auth.dependencies")
deps_mod.get_current_user_id = lambda: 1
deps_mod.require_permission = lambda roles: (lambda: None)
auth_mod.dependencies = deps_mod
sys.modules["auth"] = auth_mod
sys.modules["auth.dependencies"] = deps_mod

# Stub services package to avoid database initialisation
services_pkg = types.ModuleType("services")
band_service_stub = types.ModuleType("band_service")
services_pkg.band_service = band_service_stub
tour_service_stub = types.ModuleType("tour_service")

class _TourService:
    def get_band_recorded_count(self, band_id: int) -> int:  # pragma: no cover - stub
        return 0

tour_service_stub.TourService = _TourService
tour_service_stub.MAX_RECORDINGS_PER_YEAR = 5
services_pkg.tour_service = tour_service_stub

sys.modules["services"] = services_pkg
sys.modules["services.band_service"] = band_service_stub
sys.modules["services.tour_service"] = tour_service_stub

from routes import band  # type: ignore
MAX_RECORDINGS_PER_YEAR = band.MAX_RECORDINGS_PER_YEAR


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(band.router)
    return app


def test_recording_slots(monkeypatch):
    app = create_app()
    client = TestClient(app)

    # simulate that the band has already recorded two shows this year
    monkeypatch.setattr(band.tour_service, "get_band_recorded_count", lambda band_id: 2)

    res = client.get("/bands/1/recording-slots")
    assert res.status_code == 200
    assert res.json() == {"remaining_slots": MAX_RECORDINGS_PER_YEAR - 2}
