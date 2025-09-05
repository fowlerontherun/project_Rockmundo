from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.routes import admin_drug_routes


def test_admin_drug_routes_require_admin(monkeypatch):
    app = FastAPI()
    app.include_router(admin_drug_routes.router)

    async def fail_require_admin() -> None:
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    async def noop_audit_dependency():
        return None

    app.dependency_overrides[admin_drug_routes.require_admin] = fail_require_admin
    app.dependency_overrides[admin_drug_routes.audit_dependency] = noop_audit_dependency

    client = TestClient(app)
    assert client.get("/drug-categories").status_code == 403
    assert client.get("/drugs").status_code == 403
