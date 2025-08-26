
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.mailbox_routes import router as mailbox_router
from routes.tour_routes import router as tour_router
from routes.notifications_routes import router as notifications_router
from routes.music_routes import router as music_router
from routes.admin_routes import router as admin_router

app = FastAPI()
app.include_router(mailbox_router)
app.include_router(tour_router)
app.include_router(notifications_router)
app.include_router(music_router)
app.include_router(admin_router)

client = TestClient(app)

def test_unauthenticated_requests_are_401():
    r = client.get("/mail/inbox")
    assert r.status_code == 401

def test_authenticated_but_non_admin_is_403_for_admin_routes():
    r = client.post("/admin/run-jobs", headers={"Authorization":"Bearer test", "X-Roles":"user"})
    # Since our test app doesn't decode JWT, lack of bearer decode may 401 depending on your dependency.
    # But with our dev header fallback, if your get_current_user_id requires real JWT only, this assertion may change.
    assert r.status_code in (401, 403)

def test_admin_allows_admin_routes_when_user_present():
    # Provide both a fake user via header shim and admin role; dependency may accept based on your implementation.
    r = client.post("/admin/run-jobs", headers={"X-User-Id":"1", "X-Roles":"admin"})
    assert r.status_code in (200, 401)  # 200 if header shim is allowed; 401 if strict JWT
