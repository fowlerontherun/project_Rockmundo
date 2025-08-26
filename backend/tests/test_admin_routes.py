import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_admin_health_requires_auth(monkeypatch):
    # monkeypatch get_current_user_id to always raise 401
    from backend.routes import admin_routes
    monkeypatch.setattr(admin_routes, "get_current_user_id", lambda: (_ for _ in ()).throw(Exception("Auth not configured")))
    resp = client.get("/admin/health")
    assert resp.status_code in (401, 403)

def test_world_pulse_health_requires_auth(monkeypatch):
    from backend.routes import world_pulse_routes
    monkeypatch.setattr(world_pulse_routes, "get_current_user_id", lambda: (_ for _ in ()).throw(Exception("Auth not configured")))
    resp = client.get("/world-pulse/health")
    assert resp.status_code in (401, 403)
