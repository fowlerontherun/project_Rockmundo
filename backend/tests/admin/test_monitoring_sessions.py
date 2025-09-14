from fastapi import FastAPI
from fastapi.testclient import TestClient
import backend.routes.admin_monitoring_routes as monitoring_routes
from services.session_service import SessionService, get_session_service


def create_app(svc: SessionService) -> TestClient:
    app = FastAPI()
    app.include_router(monitoring_routes.router)
    app.dependency_overrides[monitoring_routes.get_session_service] = lambda: svc

    async def fake_current_user_id(_req):
        return 1

    async def fake_require_permission(_roles, _uid):
        return True

    monitoring_routes.get_current_user_id = fake_current_user_id
    monitoring_routes.require_permission = fake_require_permission
    return TestClient(app)


def test_list_and_terminate_sessions(tmp_path):
    db_path = tmp_path / 'sessions.db'
    svc = SessionService(db_path)
    svc.add_session('s1', 1, '127.0.0.1', 'ua')
    svc.add_session('s2', 2, '127.0.0.2', 'ua2')

    client = create_app(svc)

    resp = client.get('/monitoring/sessions')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    resp = client.delete('/monitoring/sessions/s1')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'terminated'

    resp = client.get('/monitoring/sessions')
    assert len(resp.json()) == 1

    resp = client.delete('/monitoring/sessions/doesnotexist')
    assert resp.status_code == 404
